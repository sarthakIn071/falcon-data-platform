import re
from typing import Any

from data_quality.rules import DQRule, DQRuleSet
from pydantic import BaseModel, Field


class DQRuleResult(BaseModel):
    rule_id: int
    field_name: str
    rule_type: str
    severity: str
    passed: bool
    message: str | None = None


class DQResult(BaseModel):
    passed: bool
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_count: int = 0
    error_count: int = 0
    rule_results: list[DQRuleResult] = Field(default_factory=list)


class DQEngine:
    """
    Evaluates data quality rules against a record.
    """

    def evaluate(
        self,
        record: dict[str, Any],
        rule_set: DQRuleSet,
    ) -> DQResult:

        rule_results: list[DQRuleResult] = []

        for rule in rule_set.rules:
            if not rule.enabled:
                continue

            passed, message = self._evaluate_rule(record, rule)

            rule_results.append(
                DQRuleResult(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    passed=passed,
                    message=message,
                )
            )

        passed_rules = sum(
            1 for result in rule_results if result.passed
        )

        failed_rules = len(rule_results) - passed_rules

        warning_count = sum(
            1
            for result in rule_results
            if not result.passed and result.severity == "WARNING"
        )

        error_count = sum(
            1
            for result in rule_results
            if not result.passed and result.severity == "ERROR"
        )

        return DQResult(
            passed=error_count  == 0,
            total_rules=len(rule_results),
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warning_count=warning_count,
            error_count=error_count,
            rule_results=rule_results,
        )

    def _evaluate_rule(
        self,
        record: dict[str, Any],
        rule: DQRule,
    ) -> tuple[bool, str | None]:

        value = record.get(rule.field_name)

        if rule.rule_type == "NOT_NULL":
            return self._not_null(value)

        if rule.rule_type == "NOT_BLANK":
            return self._not_blank(value)

        if rule.rule_type == "POSITIVE":
            return self._positive(value)

        if rule.rule_type == "EMAIL":
            return self._email(value)

        if rule.rule_type == "MIN_LENGTH":
            return self._min_length(value, rule.rule_value)

        if rule.rule_type == "MAX_LENGTH":
            return self._max_length(value, rule.rule_value)

        return (
            False,
            f"Unsupported DQ rule type: {rule.rule_type}",
        )

    @staticmethod
    def _not_null(value: Any) -> tuple[bool, str | None]:
        if value is None:
            return False, "Value cannot be null"

        return True, None

    @staticmethod
    def _not_blank(value: Any) -> tuple[bool, str | None]:
        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            return False, "Value cannot be blank"

        return True, None

    @staticmethod
    def _positive(value: Any) -> tuple[bool, str | None]:
        if value is None:
            return False, "Value must be positive"

        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False, "Value must be numeric"

        if value <= 0:
            return False, "Value must be greater than zero"

        return True, None

    @staticmethod
    def _email(value: Any) -> tuple[bool, str | None]:
        if not isinstance(value, str):
            return False, "Email must be a string"

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(pattern, value):
            return False, "Invalid email format"

        return True, None

    @staticmethod
    def _min_length(
        value: Any,
        rule_value: str | None,
    ) -> tuple[bool, str | None]:

        if value is None:
            return False, "Value cannot be null"

        if rule_value is None:
            return False, "MIN_LENGTH rule requires a value"

        if not isinstance(value, str):
            return False, "Value must be a string"

        minimum = int(rule_value)

        if len(value) < minimum:
            return (
                False,
                f"Value must have at least {minimum} characters",
            )

        return True, None


    @staticmethod
    def _max_length(
        value: Any,
        rule_value: str | None,
    ) -> tuple[bool, str | None]:

        if value is None:
            return False, "Value cannot be null"

        if rule_value is None:
            return False, "MAX_LENGTH rule requires a value"

        if not isinstance(value, str):
            return False, "Value must be a string"

        maximum = int(rule_value)

        if len(value) > maximum:
            return (
                False,
                f"Value must have at most {maximum} characters",
            )

        return True, None