from config.settings import settings
from data_quality.engine import DQEngine
from data_quality.repository import DQRuleRepository


def get_engine_and_rules():
    repository = DQRuleRepository(settings.database_url)
    rule_set = repository.get_rule_set(1)
    engine = DQEngine()

    return engine, rule_set


def test_dq_engine_all_rules_pass():
    engine, rule_set = get_engine_and_rules()

    record = {
    "customer_id": 1001,
    "name": "John",
    "email": "john@example.com",
    }

    result = engine.evaluate(record, rule_set)

    assert result.passed is True
    assert result.total_rules == 5
    assert result.passed_rules == 5
    assert result.failed_rules == 0
    assert result.warning_count == 0
    assert result.error_count == 0


def test_dq_engine_positive_rule_fails():
    engine, rule_set = get_engine_and_rules()

    record = {
        "customer_id": -10,
        "name": "John",
        "email": "john@example.com",
    }

    result = engine.evaluate(record, rule_set)

    assert result.passed is False
    assert result.failed_rules == 1
    assert result.error_count == 1

    failed = [
        rule for rule in result.rule_results
        if not rule.passed
    ]

    assert len(failed) == 1
    assert failed[0].field_name == "customer_id"
    assert failed[0].rule_type == "POSITIVE"


def test_dq_engine_not_blank_rule_fails():
    engine, rule_set = get_engine_and_rules()

    record = {
        "customer_id": 1001,
        "name": "",
        "email": "john@example.com",
    }

    result = engine.evaluate(record, rule_set)

    assert result.passed is False
    assert result.failed_rules == 2
    assert result.error_count == 2

    failed = [
        rule for rule in result.rule_results
        if not rule.passed
    ]

    assert len(failed) == 2

    failed_types = {rule.rule_type for rule in failed}

    assert "NOT_BLANK" in failed_types
    assert "MIN_LENGTH" in failed_types


def test_dq_engine_email_warning():
    engine, rule_set = get_engine_and_rules()

    record = {
        "customer_id": 1001,
        "name": "John",
        "email": "invalid-email",
    }

    result = engine.evaluate(record, rule_set)

    assert result.passed is True
    assert result.failed_rules == 1
    assert result.warning_count == 1
    assert result.error_count == 0

    failed = [
        rule for rule in result.rule_results
        if not rule.passed
    ]

    assert failed[0].field_name == "email"
    assert failed[0].rule_type == "EMAIL"
    assert failed[0].severity == "WARNING"


def test_dq_engine_multiple_failures():
    engine, rule_set = get_engine_and_rules()

    record = {
        "customer_id": -10,
        "name": "",
        "email": "invalid-email",
    }

    result = engine.evaluate(record, rule_set)

    assert result.passed is False
    assert result.total_rules == 5
    assert result.passed_rules == 1
    assert result.failed_rules == 4
    assert result.warning_count == 1
    assert result.error_count == 3

    failed = [
        rule for rule in result.rule_results
        if not rule.passed
    ]

    assert len(failed) == 4

    failed_types = {rule.rule_type for rule in failed}

    assert "POSITIVE" in failed_types
    assert "NOT_BLANK" in failed_types
    assert "MIN_LENGTH" in failed_types
    assert "EMAIL" in failed_types

def test_dq_engine_min_length_fails():
    engine, rule_set = get_engine_and_rules()

    record = {
        "customer_id": 1001,
        "name": "Jo",
        "email": "john@example.com",
    }

    result = engine.evaluate(record, rule_set)

    failed = [
        rule for rule in result.rule_results
        if not rule.passed
    ]

    assert any(
        rule.rule_type == "MIN_LENGTH"
        for rule in failed
    )


def test_dq_engine_max_length_fails():
    engine, rule_set = get_engine_and_rules()

    record = {
        "customer_id": 1001,
        "name": "A" * 101,
        "email": "john@example.com",
    }

    result = engine.evaluate(record, rule_set)

    failed = [
        rule for rule in result.rule_results
        if not rule.passed
    ]

    assert any(
        rule.rule_type == "MAX_LENGTH"
        for rule in failed
    )