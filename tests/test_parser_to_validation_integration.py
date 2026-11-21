
import json
from io import BytesIO

from parsers.json_parser import JSONParser
from parsers.models import ParserConfig
from processing.record_processor import RecordProcessor
from validation.quarantine import QuarantineStore
from validation.rules import ValidationRule, ValidationRuleSet
from validation.service import ValidationService
from validation.validator import SchemaValidator


def test_json_parser_to_validation_and_quarantine(tmp_path):
    # 1. Configure the actual validation rules.
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
        ],
    )

    # 2. Create real validation and quarantine components.
    quarantine_store = QuarantineStore(
        base_path=str(tmp_path / "quarantine")
    )

    validation_service = ValidationService(
        validator=SchemaValidator(rule_set),
        quarantine_store=quarantine_store,
    )

    # 3. Create the actual parser and processor.
    parser = JSONParser()

    processor = RecordProcessor(
        validation_service=validation_service,
        run_id="integration-run-001",
        pipeline_id=100,
        entity="customer",
        source_type="REST_API",
        source_name="integration-test",
        file_name="customers.ndjson",
    )

    # 4. Prepare a stream containing three different cases:
    #    - Valid JSON and valid schema.
    #    - Invalid JSON.
    #    - Valid JSON but invalid schema.
    input_data = (
        b'{"customer_id": 1001, "name": "John"}\n'
        b'{"customer_id": \n'
        b'{"name": "Alice"}\n'
    )

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    # 5. Execute the complete parse-to-validation flow.
    stream = BytesIO(input_data)

    parse_results = parser.parse_stream(
    stream,
    config,
    )
    processing_results = list(
        processor.process(parse_results)
    )

    # 6. Verify processing outcomes.
    assert len(processing_results) == 3

    assert [
        result.status for result in processing_results
    ] == [
        "SUCCESS",
        "PARSING_FAILED",
        "VALIDATION_FAILED",
    ]

    assert [
        result.record_number for result in processing_results
    ] == [1, 2, 3]

    # 7. Verify the actual quarantine files.
    quarantine_directory = (
        tmp_path
        / "quarantine"
        / "records"
        / "integration-run-001"
    )

    quarantine_files = list(
        quarantine_directory.glob("*.json")
    )

    assert len(quarantine_files) == 2

    quarantined_records = [
        json.loads(file.read_text(encoding="utf-8"))
        for file in quarantine_files
    ]

    parsing_failure = next(
        record
        for record in quarantined_records
        if record["error_stage"] == "PARSING"
    )

    validation_failure = next(
        record
        for record in quarantined_records
        if record["reason"] == "Schema validation failed"
    )

    assert parsing_failure["raw_data"] == '{"customer_id": \n'
    assert parsing_failure["record_number"] == 2
    assert parsing_failure["run_id"] == "integration-run-001"

    assert validation_failure["original_data"] == {
        "name": "Alice"
    }
    assert validation_failure["run_id"] == "integration-run-001"
    assert validation_failure["entity"] == "customer"
