from config.settings import settings
from data_quality.repository import DQRuleRepository
from processing.dq_processor import DQBatchProcessor


from uuid import uuid4

from data_quality.models import DQExecutionContext

def get_context():
    return DQExecutionContext(
        pipeline_id=10,
        run_id=uuid4(),
        step_id=25,
    )

def get_rule_set():
    repository = DQRuleRepository(settings.database_url)
    return repository.get_rule_set(1)


def test_processor_processes_full_batch():
    processor = DQBatchProcessor(
        rule_set=get_rule_set(),
        batch_size=2,
        timeout_seconds=30,
        context=get_context(),
    )

    record_1 = {
        "customer_id": 1001,
        "name": "John",
        "email": "john@example.com",
    }

    record_2 = {
        "customer_id": 1002,
        "name": "Sarah",
        "email": "sarah@example.com",
    }

    assert processor.add_record(record_1) == []

    results = processor.add_record(record_2)

    assert len(results) == 1

    batch_result = results[0]

    assert batch_result.total_records == 2
    assert batch_result.passed_records == 2
    assert batch_result.failed_records == 0


def test_processor_flushes_partial_batch():
    processor = DQBatchProcessor(
        rule_set=get_rule_set(),
        batch_size=3,
        timeout_seconds=30,
        context=get_context(),
    )

    processor.add_record(
        {
            "customer_id": 1001,
            "name": "John",
            "email": "john@example.com",
        }
    )

    result = processor.flush()

    assert result is not None
    assert result.total_records == 1
    assert result.passed_records == 1


def test_processor_flush_empty_batch():
    processor = DQBatchProcessor(
        rule_set=get_rule_set(),
        batch_size=3,
        timeout_seconds=30,
        context=get_context(),
    )

    result = processor.flush()

    assert result is None   