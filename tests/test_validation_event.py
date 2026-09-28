from validation.quarantine import QuarantineStore
from validation.rules import ValidationRule, ValidationRuleSet
from validation.service import ValidationService
from validation.validator import SchemaValidator
from messaging.event import FalconEvent, SourceInfo


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

    return ValidationService(
        validator=SchemaValidator(rule_set),
        quarantine_store=QuarantineStore(
            base_path=str(tmp_path)
        ),
    )


def test_invalid_falcon_event_is_quarantined(tmp_path):
    service = create_service(tmp_path)

    event = FalconEvent(
        event_id="customer-1001",
        run_id="run-001",
        source=SourceInfo(
            type="REST_API",
            connector="rest_connector",
            system="customer-api",
        ),
        entity="customer",
        payload={
            "customer_id": "1001",
            "name": "John",
        },
    )

    result = service.validate_event(event)

    assert result.valid is False

    quarantine_files = list(
        (tmp_path / "records" / "run-001").glob("*.json")
    )

    assert len(quarantine_files) == 1