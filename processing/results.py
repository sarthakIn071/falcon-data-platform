
from dataclasses import dataclass
from typing import Literal

from validation.models import ValidationResult


ProcessingStatus = Literal[
    "SUCCESS",
    "VALIDATION_FAILED",
    "PARSING_FAILED",
]


@dataclass
class RecordProcessingResult:
    """
    Outcome of parsing and validating one input record.
    """

    record_number: int
    status: ProcessingStatus
    validation_result: ValidationResult | None = None
    quarantine_reference: str | None = None
    error: str | None = None
