from datetime import datetime,timezone
from typing import Any

from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    type:str
    connector:str
    system:str | None = None


class FalconEvent(BaseModel):
    event_id:str
    event_time: datetime = Field(
        default_factory=lambda:datetime.now(timezone.utc)
    )


    run_id :str

    source: SourceInfo

    entity: str

    operation: str = "UPSERT"

    schema_version: str = "1.0"

    payload: dict[str,Any]

    metadata: dict[str,Any] = Field(default_factory=dict)
