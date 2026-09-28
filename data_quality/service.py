from typing import Any

from pydantic import BaseModel

from data_quality.engine import DQEngine, DQResult
from data_quality.rules import DQRuleSet


class DQBatchResult(BaseModel):
    """
    Aggregated Data Quality result for a batch of records.
    """

    total_records: int
    passed_records: int
    failed_records: int
    warning_count: int
    error_count: int
    results: list[DQResult]


class DQExecutionService:
    """
    Executes Data Quality checks for a batch of records.
    """

    def __init__(self, engine: DQEngine):
        self.engine = engine

    def evaluate_batch(
        self,
        records: list[dict[str, Any]],
        rule_set: DQRuleSet,
    ) -> DQBatchResult:

        results: list[DQResult] = []

        for record in records:
            result = self.engine.evaluate(
                record,
                rule_set,
            )
            results.append(result)

        passed_records = sum(
            1 for result in results if result.passed
        )

        failed_records = len(results) - passed_records

        warning_count = sum(
            result.warning_count
            for result in results
        )

        error_count = sum(
            result.error_count
            for result in results
        )

        return DQBatchResult(
            total_records=len(results),
            passed_records=passed_records,
            failed_records=failed_records,
            warning_count=warning_count,
            error_count=error_count,
            results=results,
        )