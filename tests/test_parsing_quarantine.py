
import json

from validation.quarantine import QuarantineStore
from validation.rules import ValidationRule, ValidationRuleSet
from validation.service import ValidationService
from validation.validator import SchemaValidator


def create_service(tmp_path):
    rule_set = ValidationRuleSet(
        schema_version="1.0",
        rules=[],
    )

    return ValidationService(
        validator=SchemaValidator(rule_set),
        quarantine_store=QuarantineStore(
            base_path=str(tmp_path)
        ),
    )


def test_parsing_error_is_quarantined(tmp_path):
    service = create_service(tmp_path)

    raw_data = b'{"customer_id": INVALID}'

    path = service.quarantine_parse_error(
        raw_data=raw_data,
        record_number=3,
        error="Invalid JSON on line 3",
        run_id="run-001",
        pipeline_id=1,
        entity="customer",
        file_name="customers.ndjson",
    )

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["quarantine_type"] == "RECORD"
    assert data["run_id"] == "run-001"
    assert data["pipeline_id"] == 1
    assert data["record_number"] == 3
    assert data["error_stage"] == "PARSING"
    assert data["raw_data"] == raw_data.decode("utf-8")
    assert data["errors"][0]["code"] == "PARSE_ERROR"
    assert data["errors"][0]["message"] == "Invalid JSON on line 3"
