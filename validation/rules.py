from typing import Literal

from pydantic import BaseModel, Field


class ValidationRule(BaseModel):
    """
    Defines a validation rule for a single field.
    """

    field: str
    required: bool = False
    type: Literal["string", "integer", "float", "boolean", "object", "array"] | None = None


class ValidationRuleSet(BaseModel):
    """
    Collection of validation rules for a pipeline.
    """

    schema_version: str = "1.0"

    rules: list[ValidationRule] = Field(default_factory=list)