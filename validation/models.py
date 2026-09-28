from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    field: str | None = None
    code: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class QuarantineRecord(BaseModel):
    quarantine_id: str
    quarantine_type: str  # RECORD or FILE

    event_id: str | None = None
    run_id: str
    pipeline_id: int | None = None

    entity: str | None = None
    source_type: str | None = None
    source_name: str | None = None

    file_name: str | None = None
    file_path: str | None = None

    reason: str

    errors: list[ValidationError] = Field(default_factory=list)

    original_data: dict[str, Any] | None = None

    quarantined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )