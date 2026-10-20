from pathlib import Path
from typing import BinaryIO, Protocol


class FileStorage(Protocol):
    async def save(self, stored_name: str, source: BinaryIO) -> int:
        """Copy ``source`` into the storage under ``stored_name``; return the number of bytes written."""
        ...

    async def delete(self, stored_name: str) -> None:
        """Remove the file; a missing file is not an error."""
        ...

    async def exists(self, stored_name: str) -> bool: ...

    def local_path(self, stored_name: str) -> Path:
        """Filesystem path of the file.

        The one local-disk-specific method: ``FileResponse`` and the metadata
        extractor need a path.  An object-storage backend would download to a
        temp file here (or the two callers would be switched to streams).
        """
        ...
