"""Dependency wiring: the only place where concrete implementations are assembled for requests."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.file_storage import get_storage
from src.repositories.alerts import AlertRepository
from src.repositories.files import FileRepository
from src.services.alerts import AlertService
from src.services.files import FileService
from src.tasks.processing import enqueue_file_processing

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_file_service(session: SessionDep) -> FileService:
    return FileService(
        session=session,
        files=FileRepository(session),
        alerts=AlertRepository(session),
        storage=get_storage(),
        enqueue_processing=enqueue_file_processing,
    )


def get_alert_service(session: SessionDep) -> AlertService:
    return AlertService(alerts=AlertRepository(session))


FileServiceDep = Annotated[FileService, Depends(get_file_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
