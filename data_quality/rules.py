from typing import Any

from pydantic import BaseModel, Field


class DQRule(BaseModel):
    rule_id: int
    field_name: str
    rule_type: str
    severity: str = "ERROR"

    rule_value: str | None = None
    rule_values: list[Any] = Field(default_factory=list)

    description: str | None = None
    enabled: bool = True


class DQRuleSet(BaseModel):
    rule_set_id: int
    rule_set_name: str
    description: str | None = None
    version: int
    status: str
    rules: list[DQRule] = Field(default_factory=list)