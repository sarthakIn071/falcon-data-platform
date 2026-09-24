from typing import Any

from pydantic import BaseModel,Field

class ConnectorConfig(BaseModel):

    """
    Generic Configuration For a  falcon source connector
    """

    name:str
    connector_type:str
    source_type:str

    config: dict[str,Any] = Field(default_factory=dict)

    enabled: bool = True


class ConnectorContext(BaseModel):
    """
    Runtime context available to a connector execution.
    """

    pipeline_id: int | None = None
    run_id: str | None = None

    entity: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)