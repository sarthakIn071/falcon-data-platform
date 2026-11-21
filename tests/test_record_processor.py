
from types import SimpleNamespace

from parsers.results import ParseResult
from processing.record_processor import RecordProcessor


class FakeValidationService:

    def __init__(self):
        self.validated_records = []
        self.quarantined_records = []

    def validate_record(self, **kwargs):
        self.validated_records.append(kwargs)

        record = kwargs["record"]

        return SimpleNamespace(
            valid=record.get("customer_id") is not None
        )

    def quarantine_parse_error(self, **kwargs):
        self.quarantined_records.append(kwargs)
        return "quarantine-123"


def make_processor():
    service = FakeValidationService()

    processor = RecordProcessor(
        validation_service=service,
        run_id="run-001",
        pipeline_id=10,
        entity="customer",
        source_type="REST_API",
        source_name="demo",
        file_name="customers.json",
    )

    return processor, service


def test_process_valid_record():
    processor, service = make_processor()

    parse_results = [
        ParseResult(
            record={"customer_id": 1001, "name": "John"},
            record_number=1,
            raw_data=b'{"customer_id": 1001, "name": "John"}',
        )
    ]

    results = list(processor.process(parse_results))

    assert len(results) == 1
    assert results[0].status == "SUCCESS"
    assert results[0].record_number == 1
    assert results[0].validation_result.valid is True

    assert len(service.validated_records) == 1
    assert len(service.quarantined_records) == 0


def test_process_validation_failure():
    processor, service = make_processor()

    parse_results = [
        ParseResult(
            record={"name": "John"},
            record_number=2,
            raw_data=b'{"name": "John"}',
        )
    ]

    results = list(processor.process(parse_results))

    assert len(results) == 1
    assert results[0].status == "VALIDATION_FAILED"
    assert results[0].record_number == 2
    assert results[0].validation_result.valid is False

    assert len(service.validated_records) == 1
    assert len(service.quarantined_records) == 0


def test_process_parsing_failure():
    processor, service = make_processor()

    parse_results = [
        ParseResult(
            record=None,
            record_number=3,
            raw_data=b'{"customer_id": ',
            error="Invalid JSON",
        )
    ]

    results = list(processor.process(parse_results))

    assert len(results) == 1
    assert results[0].status == "PARSING_FAILED"
    assert results[0].record_number == 3
    assert results[0].error == "Invalid JSON"
    assert results[0].quarantine_reference == "quarantine-123"

    assert len(service.validated_records) == 0
    assert len(service.quarantined_records) == 1
    assert service.quarantined_records[0]["raw_data"] == b'{"customer_id": '


def test_process_continues_after_parsing_failure():
    processor, service = make_processor()

    parse_results = [
        ParseResult(
            record={"customer_id": 1001},
            record_number=1,
            raw_data=b'{"customer_id": 1001}',
        ),
        ParseResult(
            record=None,
            record_number=2,
            raw_data=b'{"customer_id": ',
            error="Invalid JSON",
        ),
        ParseResult(
            record={"customer_id": 1003},
            record_number=3,
            raw_data=b'{"customer_id": 1003}',
        ),
    ]

    results = list(processor.process(parse_results))

    assert [result.status for result in results] == [
        "SUCCESS",
        "PARSING_FAILED",
        "SUCCESS",
    ]

    assert [result.record_number for result in results] == [1, 2, 3]

    assert len(service.validated_records) == 2
    assert len(service.quarantined_records) == 1
