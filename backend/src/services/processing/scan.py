"""Threat scan rules.  Pure function: no I/O, no database."""

from dataclasses import dataclass
from pathlib import Path

from src.core.enums import ScanStatus

SUSPICIOUS_EXTENSIONS = frozenset({".exe", ".bat", ".cmd", ".sh", ".js"})
MAX_SAFE_SIZE_BYTES = 10 * 1024 * 1024
PDF_MIME_TYPES = frozenset({"application/pdf", "application/octet-stream"})


@dataclass(frozen=True, slots=True)
class ScanVerdict:
    status: ScanStatus
    details: str
    requires_attention: bool


def scan_file(*, original_name: str, size: int, mime_type: str) -> ScanVerdict:
    reasons: list[str] = []
    extension = Path(original_name).suffix.lower()

    if extension in SUSPICIOUS_EXTENSIONS:
        reasons.append(f"suspicious extension {extension}")

    if size > MAX_SAFE_SIZE_BYTES:
        reasons.append("file is larger than 10 MB")

    if extension == ".pdf" and mime_type not in PDF_MIME_TYPES:
        reasons.append("pdf extension does not match mime type")

    if reasons:
        return ScanVerdict(ScanStatus.SUSPICIOUS, ", ".join(reasons), True)
    return ScanVerdict(ScanStatus.CLEAN, "no threats found", False)
