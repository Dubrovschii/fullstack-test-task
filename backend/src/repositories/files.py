from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recent(self) -> list[StoredFile]:
        result = await self._session.scalars(select(StoredFile).order_by(StoredFile.created_at.desc()))
        return list(result.all())

    async def get(self, file_id: str) -> StoredFile | None:
        return await self._session.get(StoredFile, file_id)

    def add(self, file: StoredFile) -> None:
        self._session.add(file)

    async def delete(self, file: StoredFile) -> None:
        await self._session.delete(file)
