"""Which alert a processed file produces.  Pure function."""

from dataclasses import dataclass

from src.core.enums import AlertLevel, ProcessingStatus


@dataclass(frozen=True, slots=True)
class AlertDraft:
    level: AlertLevel
    message: str


def build_alert(*, processing_status: str, requires_attention: bool, scan_details: str | None) -> AlertDraft:
    if processing_status == ProcessingStatus.FAILED:
        return AlertDraft(AlertLevel.CRITICAL, "File processing failed")
    if requires_attention:
        return AlertDraft(AlertLevel.WARNING, f"File requires attention: {scan_details}")
    return AlertDraft(AlertLevel.INFO, "File processed successfully")
