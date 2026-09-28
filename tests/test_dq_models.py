from data_quality.engine import DQResult, DQRuleResult

from uuid import uuid4

from data_quality.models import DQExecutionContext

def test_dq_rule_result():
    result = DQRuleResult(
        rule_id=1,
        field_name="customer_id",
        rule_type="POSITIVE",
        severity="ERROR",
        passed=False,
        message="Value must be positive",
    )

    assert result.rule_id == 1
    assert result.field_name == "customer_id"
    assert result.passed is False
    assert result.severity == "ERROR"


def test_dq_result():
    result = DQResult(
        passed=False,
        total_rules=3,
        passed_rules=1,
        failed_rules=2,
        warning_count=1,
        error_count=1,
    )

    assert result.passed is False
    assert result.total_rules == 3
    assert result.passed_rules == 1
    assert result.failed_rules == 2
    assert result.warning_count == 1
    assert result.error_count == 1

def test_dq_execution_context():
    run_id = uuid4()

    context = DQExecutionContext(
        pipeline_id=10,
        run_id=run_id,
        step_id=25,
    )

    assert context.pipeline_id == 10
    assert context.run_id == run_id
    assert context.step_id == 25