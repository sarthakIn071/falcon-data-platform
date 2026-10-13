from typing import Any

from pydantic import BaseModel

class KafkaRecord(BaseModel):
    value: dict[str, Any]
    topic: str
    partition: int
    offset: int

class KafkaBatch(BaseModel):
    records: list[dict[str, Any]]
    topic: str
    partition: int
    first_offset: int
    last_offset: int