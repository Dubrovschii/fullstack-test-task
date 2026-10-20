"""Binary file storage behind a small interface (local disk today, object storage later)."""

from functools import lru_cache

from src.core.config import get_settings
from src.file_storage.base import FileStorage
from src.file_storage.local import LocalFileStorage


@lru_cache
def get_storage() -> FileStorage:
    return LocalFileStorage(get_settings().storage_dir)


__all__ = ["FileStorage", "LocalFileStorage", "get_storage"]
