"""Status vocabularies stored in the database as plain strings.

The database columns stay ``String`` (no migration needed); the enums only
replace magic strings in the code.  Always pass ``.value`` to the ORM.
"""

from enum import StrEnum


class ProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ScanStatus(StrEnum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
