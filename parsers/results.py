from dataclasses import dataclass
from typing import Any


@dataclass
class ParseResult:
    """
    Represents the outcome of parsing one input record.
    """

    record: dict[str, Any] | None
    record_number: int
    raw_data: bytes | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None