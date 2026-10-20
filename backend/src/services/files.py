import asyncio
import mimetypes
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Protocol
from uuid import uuid4

from src.core.enums import ProcessingStatus
from src.core.exceptions import EmptyFile, FileNotFound, StoredFileMissing
from src.models import StoredFile
from src.services.naming import fit_name, safe_suffix

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.file_storage import FileStorage
    from src.repositories.alerts import AlertRepository
    from src.repositories.files import FileRepository

MIME_TYPE_MAX_LENGTH = 255


class UploadSource(Protocol):
    """What the service needs from an uploaded file (Starlette's ``UploadFile`` fits)."""

    filename: str | None
    content_type: str | None
    file: BinaryIO


class FileService:
    def __init__(
        self,
        *,
        session: "AsyncSession",
        files: "FileRepository",
        alerts: "AlertRepository",
        storage: "FileStorage",
        enqueue_processing: Callable[[str], None],
    ) -> None:
        self._session = session
        self._files = files
        self._alerts = alerts
        self._storage = storage
        self._enqueue_processing = enqueue_processing

    async def list_recent(self) -> list[StoredFile]:
        return await self._files.list_recent()

    async def get(self, file_id: str) -> StoredFile:
        file = await self._files.get(file_id)
        if file is None:
            raise FileNotFound()
        return file

    async def create(self, *, title: str, upload: UploadSource) -> StoredFile:
        file_id = str(uuid4())
        stored_name = f"{file_id}{safe_suffix(upload.filename)}"

        size = await self._storage.save(stored_name, upload.file)
        if size == 0:
            await self._storage.delete(stored_name)
            raise EmptyFile()

        file = StoredFile(
            id=file_id,
            title=title,
            original_name=fit_name(upload.filename or stored_name),
            stored_name=stored_name,
            mime_type=(upload.content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream")[
                :MIME_TYPE_MAX_LENGTH
            ],
            size=size,
            processing_status=ProcessingStatus.UPLOADED.value,
        )
        try:
            self._files.add(file)
            await self._session.commit()
            await self._session.refresh(file)
        except BaseException:
            await self._storage.delete(stored_name)  # no orphan on disk if the row was not saved
            raise

        # Publishing to the broker is blocking network I/O: keep it off the event loop.
        await asyncio.to_thread(self._enqueue_processing, file.id)
        return file

    async def update_title(self, file_id: str, title: str) -> StoredFile:
        file = await self.get(file_id)
        file.title = title
        await self._session.commit()
        await self._session.refresh(file)
        return file

    async def get_for_download(self, file_id: str) -> tuple[StoredFile, Path]:
        file = await self.get(file_id)
        if not await self._storage.exists(file.stored_name):
            raise StoredFileMissing()
        return file, self._storage.local_path(file.stored_name)

    async def delete(self, file_id: str) -> None:
        file = await self.get(file_id)
        stored_name = file.stored_name

        # alerts.file_id has a foreign key without ON DELETE: deleting a file that already had
        # an alert (i.e. any processed file) used to fail with an IntegrityError / HTTP 500.
        await self._alerts.delete_for_file(file_id)
        await self._files.delete(file)
        await self._session.commit()

        # Database first, disk second: a failed commit no longer loses the stored bytes.
        await self._storage.delete(stored_name)
