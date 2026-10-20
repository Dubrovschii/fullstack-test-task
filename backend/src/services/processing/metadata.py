"""Metadata extraction.  Blocking, file-based, dependency-free.

Both readers stream the file, so memory use does not depend on its size
(the previous code did ``read_text()`` / ``read_bytes()`` on the whole file).
"""

import mmap
import re
from pathlib import Path

TEXT_CHUNK_SIZE = 1024 * 1024

# Characters that ``str.splitlines()`` treats as line boundaries.  The file is
# opened with universal newlines, so "\r" and "\r\n" arrive as "\n" and a
# boundary is always a single character -- which makes chunked counting exact.
_LINE_BREAKS = ("\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " ")

# "/Type /Page" is a prefix of "/Type /Pages" (the page-tree root), which the
# old plain substring count also matched, over-counting every PDF by at least
# one.  Also tolerate "/Type/Page" written without a space.
_PDF_PAGE_RE = re.compile(rb"/Type\s*/Page(?![A-Za-z])")


def count_text(path: Path, chunk_size: int = TEXT_CHUNK_SIZE) -> tuple[int, int]:
    """Return ``(line_count, char_count)`` identical to ``len(text.splitlines())`` / ``len(text)``
    of ``path.read_text(encoding="utf-8", errors="ignore")``, without loading the file."""
    lines = 0
    chars = 0
    line_open = False  # the last character seen was not a line boundary

    with path.open("r", encoding="utf-8", errors="ignore") as stream:
        while chunk := stream.read(chunk_size):
            chars += len(chunk)
            lines += sum(chunk.count(separator) for separator in _LINE_BREAKS)
            line_open = chunk[-1] not in _LINE_BREAKS

    return lines + (1 if line_open else 0), chars


def count_pdf_pages(path: Path) -> int:
    """Approximate page count; never less than 1 (as before)."""
    try:
        with path.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
            count = sum(1 for _ in _PDF_PAGE_RE.finditer(mapped))
    except ValueError:  # an empty file cannot be memory-mapped
        count = 0
    return max(count, 1)


def extract_metadata(path: Path, *, original_name: str, size: int, mime_type: str) -> dict[str, object]:
    metadata: dict[str, object] = {
        "extension": Path(original_name).suffix.lower(),
        "size_bytes": size,
        "mime_type": mime_type,
    }

    if mime_type.startswith("text/"):
        line_count, char_count = count_text(path)
        metadata["line_count"] = line_count
        metadata["char_count"] = char_count
    elif mime_type == "application/pdf":
        metadata["approx_page_count"] = count_pdf_pages(path)

    return metadata
