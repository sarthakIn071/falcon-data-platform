from typing import Any

from validation.models import ValidationError, ValidationResult
from validation.rules import ValidationRuleSet


class SchemaValidator:
    """
    Executes schema validation rules against a record.
    """

    def __init__(self, rule_set: ValidationRuleSet):
        self.rule_set = rule_set

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        errors: list[ValidationError] = []

        for rule in self.rule_set.rules:
            field = rule.field

            # Required field validation
            if rule.required:
                if field not in record or record[field] is None:
                    errors.append(
                        ValidationError(
                            field=field,
                            code="REQUIRED_FIELD_MISSING",
                            message=f"Required field '{field}' is missing",
                        )
                    )
                    continue

            # Optional field that isn't present
            if field not in record:
                continue

            value = record[field]

            # Type validation
            if rule.type and not self._is_valid_type(value, rule.type):
                errors.append(
                    ValidationError(
                        field=field,
                        code="INVALID_TYPE",
                        message=(
                            f"Field '{field}' has invalid type. "
                            f"Expected '{rule.type}'. "
                            f"Got '{type(value).__name__}'."
                        ),
                    )
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )

    @staticmethod
    def _is_valid_type(value: Any, expected_type: str) -> bool:
        type_mapping = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "object": dict,
            "array": list,
        }

        python_type = type_mapping.get(expected_type)

        if python_type is None:
            return False

        # bool is a subclass of int in Python.
        # Explicitly prevent True/False from passing integer validation.
        if expected_type == "integer" and isinstance(value, bool):
            return False

        return isinstance(value, python_type)