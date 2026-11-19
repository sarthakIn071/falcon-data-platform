
from typing import Literal, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class SchemaEvolutionConfig(BaseModel):

    model_config = ConfigDict(extra="forbid")

    mode: Literal[
        "BACKWARD",
        "FORWARD",
        "FULL",
        "NONE",
    ] = "BACKWARD"


class ParserConfig(BaseModel):

    model_config = ConfigDict(extra="forbid")

    format: Literal["JSON", "AVRO"]

    schema_version: str = "1.0"
    encoding: str = "utf-8"
    record_path: str | None = None

    # JSON parsing mode
    json_mode: Literal["DOCUMENT", "LINES"] = "DOCUMENT"

    schema_evolution: SchemaEvolutionConfig = Field(
        default_factory=SchemaEvolutionConfig
    )

    schema_source: Literal["INLINE"] | None = None
    avro_schema: dict[str, Any] | None = Field(
        default=None,
        alias="schema",
    )

    @model_validator(mode="after")
    def validate_avro_configuration(self):

        if self.format == "AVRO":

            if self.schema_source != "INLINE":
                raise ValueError(
                    "AVRO currently requires schema_source='INLINE'"
                )

            if not self.avro_schema:
                raise ValueError(
                    "An inline Avro schema is required"
                )

        return self
