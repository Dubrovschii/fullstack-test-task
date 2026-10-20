import asyncio
import shutil
from pathlib import Path
from typing import BinaryIO

_COPY_CHUNK_SIZE = 1024 * 1024


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def local_path(self, stored_name: str) -> Path:
        path = (self._root / stored_name).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError(f"stored name escapes the storage root: {stored_name!r}")
        return path

    async def save(self, stored_name: str, source: BinaryIO) -> int:
        # Chunked copy in a worker thread: memory stays flat for any upload size
        # and the event loop is not blocked by disk writes.
        return await asyncio.to_thread(self._write, self.local_path(stored_name), source)

    async def delete(self, stored_name: str) -> None:
        await asyncio.to_thread(self.local_path(stored_name).unlink, missing_ok=True)

    async def exists(self, stored_name: str) -> bool:
        return await asyncio.to_thread(self.local_path(stored_name).is_file)

    @staticmethod
    def _write(path: Path, source: BinaryIO) -> int:
        try:
            with path.open("wb") as destination:
                shutil.copyfileobj(source, destination, _COPY_CHUNK_SIZE)
                return destination.tell()
        except BaseException:
            path.unlink(missing_ok=True)  # never leave a half-written file behind
            raise
