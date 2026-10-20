"""The post-upload pipeline: scan -> metadata -> alert, in ONE task and ONE session.

It used to be three Celery tasks chained with ``.delay()``.  The steps are
strictly sequential and each takes milliseconds, so the broker round trip, the
result-backend write, the new session and the repeated ``SELECT`` per step cost
more than the work itself.  Here the file row is loaded once; the visible
states are the same as before:

    uploaded --(commit 1)--> processing + scan result
             --(commit 2)--> processed | failed, metadata and the alert together

Writing the final status and the alert in one commit also removes the old
window in which a file was "processed" but its alert did not exist yet.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm.exc import StaleDataError

from src.core.enums import ProcessingStatus
from src.services.processing.alert_policy import build_alert
from src.services.processing.metadata import extract_metadata
from src.services.processing.scan import scan_file

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.file_storage import FileStorage
    from src.models import StoredFile
    from src.repositories.alerts import AlertRepository
    from src.repositories.files import FileRepository

logger = logging.getLogger(__name__)

METADATA_FAILURE_DETAILS = "stored file not found during metadata extraction"


class ProcessingPipeline:
    def __init__(
        self,
        *,
        session: "AsyncSession",
        files: "FileRepository",
        alerts: "AlertRepository",
        storage: "FileStorage",
    ) -> None:
        self._session = session
        self._files = files
        self._alerts = alerts
        self._storage = storage

    async def run(self, file_id: str) -> None:
        file = await self._files.get(file_id)
        if file is None:
            return

        self._scan(file)
        await self._session.commit()

        try:
            await self._extract_metadata(file)
            self._raise_alert(file)
            await self._session.commit()
        except StaleDataError:
            # The file was deleted while it was being processed: nothing left to update.
            await self._session.rollback()
            logger.warning("File %s was deleted during processing", file_id)

    def _scan(self, file: "StoredFile") -> None:
        verdict = scan_file(original_name=file.original_name, size=file.size, mime_type=file.mime_type)
        file.processing_status = ProcessingStatus.PROCESSING.value
        file.scan_status = verdict.status.value
        file.scan_details = verdict.details
        file.requires_attention = verdict.requires_attention

    async def _extract_metadata(self, file: "StoredFile") -> None:
        if not await self._storage.exists(file.stored_name):
            file.processing_status = ProcessingStatus.FAILED.value
            file.scan_details = METADATA_FAILURE_DETAILS
            return

        file.metadata_json = await asyncio.to_thread(
            extract_metadata,
            self._storage.local_path(file.stored_name),
            original_name=file.original_name,
            size=file.size,
            mime_type=file.mime_type,
        )
        file.processing_status = ProcessingStatus.PROCESSED.value

    def _raise_alert(self, file: "StoredFile") -> None:
        draft = build_alert(
            processing_status=file.processing_status,
            requires_attention=file.requires_attention,
            scan_details=file.scan_details,
        )
        self._alerts.add(file.id, draft.level.value, draft.message)
