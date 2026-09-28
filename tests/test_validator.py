from validation.rules import ValidationRule, ValidationRuleSet
from validation.validator import SchemaValidator


def create_validator() -> SchemaValidator:
    rule_set = ValidationRuleSet(
        schema_version="1.0",
        rules=[
            ValidationRule(
                field="customer_id",
                required=True,
                type="integer",
            ),
            ValidationRule(
                field="name",
                required=True,
                type="string",
            ),
            ValidationRule(
                field="email",
                required=True,
                type="string",
            ),
        ],
    )

    return SchemaValidator(rule_set)


def test_valid_record():
    validator = create_validator()

    result = validator.validate(
        {
            "customer_id": 1001,
            "name": "John",
            "email": "john@example.com",
        }
    )

    assert result.valid is True
    assert result.errors == []


def test_missing_required_field():
    validator = create_validator()

    result = validator.validate(
        {
            "customer_id": 1001,
            "email": "john@example.com",
        }
    )

    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "REQUIRED_FIELD_MISSING"
    assert result.errors[0].field == "name"


def test_invalid_field_type():
    validator = create_validator()

    result = validator.validate(
        {
            "customer_id": "1001",
            "name": "John",
            "email": "john@example.com",
        }
    )

    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == "INVALID_TYPE"
    assert result.errors[0].field == "customer_id"


def test_multiple_validation_errors():
    validator = create_validator()

    result = validator.validate(
        {
            "customer_id": "1001",
        }
    )

    assert result.valid is False
    assert len(result.errors) == 3

    error_codes = {error.code for error in result.errors}

    assert "INVALID_TYPE" in error_codes
    assert "REQUIRED_FIELD_MISSING" in error_codes