from config.settings import settings
from data_quality.engine import DQEngine
from data_quality.repository import DQRuleRepository
from data_quality.service import DQExecutionService


def get_service_and_rules():
    repository = DQRuleRepository(settings.database_url)
    rule_set = repository.get_rule_set(1)

    engine = DQEngine()
    service = DQExecutionService(engine)

    return service, rule_set


def test_evaluate_batch():
    service, rule_set = get_service_and_rules()

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
        {
            "customer_id": 1003,
            "name": "",
            "email": "invalid-email",
        },
    ]

    batch_result  = service.evaluate_batch(
        records,
        rule_set,
    )

    assert batch_result.total_records == 3
    assert batch_result.passed_records == 2
    assert batch_result.failed_records == 1

    assert len(batch_result.results) == 3

    assert batch_result.results[0].passed is True
    assert batch_result.results[1].passed is True
    assert batch_result.results[2].passed is False

    assert batch_result.warning_count == 1
    assert batch_result.error_count == 2