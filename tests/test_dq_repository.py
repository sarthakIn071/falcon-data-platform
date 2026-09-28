from config.settings import settings
from data_quality.repository import DQRuleRepository


def test_get_dq_rule_set():
    repository = DQRuleRepository(settings.database_url)

    rule_set = repository.get_rule_set(1)

    assert rule_set.rule_set_id == 1
    assert rule_set.rule_set_name == "Customer DQ Rules"
    assert rule_set.version == 1
    assert rule_set.status == "ACTIVE"

    assert len(rule_set.rules) == 3

    rule_fields = {rule.field_name for rule in rule_set.rules}

    assert "customer_id" in rule_fields
    assert "name" in rule_fields
    assert "email" in rule_fields