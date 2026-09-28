import json

from validation.models import QuarantineRecord, ValidationError
from validation.quarantine import QuarantineStore


def test_quarantine_record(tmp_path):
    store = QuarantineStore(base_path=str(tmp_path))

    quarantine_record = QuarantineRecord(
        quarantine_id="q-001",
        quarantine_type="RECORD",
        event_id="customer-1001",
        run_id="run-001",
        pipeline_id=1,
        entity="customer",
        source_type="REST_API",
        source_name="customer_api",
        reason="Schema validation failed",
        errors=[
            ValidationError(
                field="customer_id",
                code="INVALID_TYPE",
                message="Expected integer, got string",
            )
        ],
        original_data={
            "customer_id": "1001",
            "name": "John",
        },
    )

    path = store.quarantine_record(quarantine_record)

    quarantine_file = tmp_path / "records" / "run-001" / "q-001.json"

    assert path == str(quarantine_file)
    assert quarantine_file.exists()

    with quarantine_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["quarantine_id"] == "q-001"
    assert data["quarantine_type"] == "RECORD"
    assert data["event_id"] == "customer-1001"
    assert data["run_id"] == "run-001"
    assert data["entity"] == "customer"
    assert data["reason"] == "Schema validation failed"

    assert data["original_data"]["customer_id"] == "1001"

    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "customer_id"
    assert data["errors"][0]["code"] == "INVALID_TYPE"


def test_quarantine_file(tmp_path):
    source_file = tmp_path / "customers.csv"

    source_file.write_text(
        "customer_id,name\n"
        "1001,John\n"
        "1002,Sarah\n",
        encoding="utf-8",
    )

    store = QuarantineStore(
        base_path=str(tmp_path / "quarantine")
    )

    quarantine_record = QuarantineRecord(
        quarantine_id="q-file-001",
        quarantine_type="FILE",
        run_id="run-002",
        pipeline_id=1,
        entity="customer",
        file_name="customers.csv",
        file_path=str(source_file),
        reason="File validation failed",
        errors=[
            ValidationError(
                field="customer_id",
                code="INVALID_TYPE",
                message="Invalid customer_id type",
            )
        ],
    )

    path = store.quarantine_file(
        source_file=str(source_file),
        quarantine_record=quarantine_record,
    )

    metadata_file = (
    tmp_path
    / "quarantine"
    / "files"
    / "run-002"
    / "quarantine.json"
    )

    assert metadata_file.exists()

    with metadata_file.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata["quarantine_id"] == "q-file-001"
    assert metadata["quarantine_type"] == "FILE"
    assert metadata["run_id"] == "run-002"
    assert metadata["pipeline_id"] == 1
    assert metadata["entity"] == "customer"
    assert metadata["file_name"] == "customers.csv"
    assert metadata["reason"] == "File validation failed"

    assert len(metadata["errors"]) == 1
    assert metadata["errors"][0]["field"] == "customer_id"
    assert metadata["errors"][0]["code"] == "INVALID_TYPE"