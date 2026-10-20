from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

TITLE_MAX_LENGTH = 255  # matches files.title String(255)


class FileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    mime_type: str
    size: int
    processing_status: str
    scan_status: str | None
    scan_details: str | None
    metadata_json: dict | None
    requires_attention: bool
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    # Previously unbounded: a title over 255 chars reached Postgres and became a 500.
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
