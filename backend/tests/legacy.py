"""Verbatim copies of the ORIGINAL business rules (from the pre-refactoring src/tasks.py).

Used only by the parity tests, to prove the refactoring did not change behaviour
(except where a test says so explicitly).
"""

from pathlib import Path


def legacy_scan(original_name: str, size: int, mime_type: str) -> tuple[str, str, bool]:
    reasons: list[str] = []
    extension = Path(original_name).suffix.lower()

    if extension in {".exe", ".bat", ".cmd", ".sh", ".js"}:
        reasons.append(f"suspicious extension {extension}")

    if size > 10 * 1024 * 1024:
        reasons.append("file is larger than 10 MB")

    if extension == ".pdf" and mime_type not in {"application/pdf", "application/octet-stream"}:
        reasons.append("pdf extension does not match mime type")

    status = "suspicious" if reasons else "clean"
    details = ", ".join(reasons) if reasons else "no threats found"
    return status, details, bool(reasons)


def legacy_alert(processing_status: str, requires_attention: bool, scan_details: str | None) -> tuple[str, str]:
    if processing_status == "failed":
        return "critical", "File processing failed"
    elif requires_attention:
        return "warning", f"File requires attention: {scan_details}"
    return "info", "File processed successfully"


def legacy_text_counts(path: Path) -> tuple[int, int]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    return len(content.splitlines()), len(content)


def legacy_pdf_pages(path: Path) -> int:
    content = path.read_bytes()
    return max(content.count(b"/Type /Page"), 1)
