from validation.quarantine import QuarantineStore
from validation.rules import ValidationRule, ValidationRuleSet
from validation.service import ValidationService
from validation.validator import SchemaValidator


def create_service(tmp_path) -> ValidationService:
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

    validator = SchemaValidator(rule_set)
    quarantine_store = QuarantineStore(base_path=str(tmp_path))

    return ValidationService(
        validator=validator,
        quarantine_store=quarantine_store,
    )


def test_valid_record_is_not_quarantined(tmp_path):
    service = create_service(tmp_path)

    result = service.validate_record(
        record={
            "customer_id": 1001,
            "name": "John",
            "email": "john@example.com",
        },
        run_id="run-001",
        event_id="customer-1001",
        entity="customer",
    )

    assert result.valid is True

    quarantine_files = list(
        (tmp_path / "records").rglob("*.json")
    )

    assert quarantine_files == []


def test_invalid_record_is_quarantined(tmp_path):
    service = create_service(tmp_path)

    result = service.validate_record(
        record={
            "customer_id": "1001",
            "name": "John",
        },
        run_id="run-001",
        event_id="customer-1001",
        entity="customer",
    )

    assert result.valid is False

    quarantine_files = list(
        (tmp_path / "records" / "run-001").glob("*.json")
    )

    assert len(quarantine_files) == 1