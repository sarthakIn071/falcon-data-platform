from unittest.mock import Mock
from uuid import uuid4

from config.settings import settings
from data_quality.coordinator import DQExecutionCoordinator
from data_quality.models import DQExecutionContext
from data_quality.repository import DQRuleRepository
from data_quality.rules import DQRuleSet
from processing.dq_processor import DQBatchProcessor


def get_rule_set() -> DQRuleSet:
    repository = DQRuleRepository(settings.database_url)
    return repository.get_rule_set(1)


def test_execute_batch():
    context = DQExecutionContext(
        pipeline_id=10,
        run_id=uuid4(),
        step_id=25,
    )

    processor = DQBatchProcessor(
        rule_set=get_rule_set(),
        context=context,
        batch_size=10,
        timeout_seconds=30,
    )

    repository = Mock()
    repository.create_step_run.return_value = 100

    coordinator = DQExecutionCoordinator(
        processor=processor,
        repository=repository,
        context=context,
    )

    records = [
        {
            "customer_id": 1001,
            "name": "John",
            "email": "john@example.com",
        },
        {
            "customer_id": 1002,
            "name": "Sarah",
            "email": "sarah@example.com",
        },
    ]

    result = coordinator.execute_batch(records)

    assert result.total_records == 2
    assert result.passed_records == 2
    assert result.failed_records == 0
    assert result.error_count == 0

    repository.create_step_run.assert_called_once()
    repository.finalize_step_run.assert_called_once()


def test_execute_batch_with_dq_errors():
    context = DQExecutionContext(
        pipeline_id=10,
        run_id=uuid4(),
        step_id=25,
    )

    processor = DQBatchProcessor(
        rule_set=get_rule_set(),
        context=context,
        batch_size=10,
        timeout_seconds=30,
    )

    repository = Mock()
    repository.create_step_run.return_value = 101

    coordinator = DQExecutionCoordinator(
        processor=processor,
        repository=repository,
        context=context,
    )

    records = [
        {
            "customer_id": -10,
            "name": "",
            "email": "invalid-email",
        },
        {
            "customer_id": 1002,
            "name": "Sarah",
            "email": "sarah@example.com",
        },
    ]

    result = coordinator.execute_batch(records)

    assert result.total_records == 2
    assert result.passed_records == 1
    assert result.failed_records == 1
    assert result.error_count > 0

    repository.create_step_run.assert_called_once()
    repository.finalize_step_run.assert_called_once()

    call_kwargs = repository.finalize_step_run.call_args.kwargs

    assert call_kwargs["step_run_id"] == 101
    assert call_kwargs["status"] == "FAILED"
    assert call_kwargs["input_count"] == 2
    assert call_kwargs["output_count"] == 1