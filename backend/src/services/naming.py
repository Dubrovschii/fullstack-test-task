"""Pure helpers for file names coming from clients."""

from pathlib import Path

MAX_NAME_LENGTH = 255  # files.original_name / files.stored_name are String(255)
MAX_SUFFIX_LENGTH = 16


def safe_suffix(filename: str | None) -> str:
    """Extension to keep in the stored name; an absurdly long one is dropped."""
    suffix = Path(filename or "").suffix
    return suffix if len(suffix) <= MAX_SUFFIX_LENGTH else ""


def fit_name(name: str, limit: int = MAX_NAME_LENGTH) -> str:
    """Shorten ``name`` to ``limit`` characters, keeping the extension.

    The scan decides by extension, so truncating the tail of a long
    "....exe" name would silently turn a suspicious file into a clean one.
    """
    if len(name) <= limit:
        return name
    suffix = Path(name).suffix
    if len(suffix) >= limit:
        return name[:limit]
    return name[: limit - len(suffix)] + suffix
