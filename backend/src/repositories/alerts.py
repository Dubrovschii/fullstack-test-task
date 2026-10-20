from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recent(self) -> list[Alert]:
        # ``id`` breaks ties between alerts created in the same instant.
        result = await self._session.scalars(select(Alert).order_by(Alert.created_at.desc(), Alert.id.desc()))
        return list(result.all())

    def add(self, file_id: str, level: str, message: str) -> Alert:
        alert = Alert(file_id=file_id, level=level, message=message)
        self._session.add(alert)
        return alert

    async def delete_for_file(self, file_id: str) -> None:
        await self._session.execute(delete(Alert).where(Alert.file_id == file_id))
