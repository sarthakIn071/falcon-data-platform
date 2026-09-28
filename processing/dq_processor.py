from typing import Any

from data_quality.engine import DQEngine
from data_quality.rules import DQRuleSet
from data_quality.service import DQBatchResult, DQExecutionService
from processing.batch import BatchBuilder

from data_quality.models import DQExecutionContext

class DQBatchProcessor:
    """
    Coordinates batch collection and Data Quality execution.
    """

    def __init__(
    self,
    rule_set: DQRuleSet,
    context: DQExecutionContext,
    batch_size: int = 1000,
    timeout_seconds: float = 30.0,
    ):
        self.rule_set = rule_set
        self.context = context

        self.batch_builder = BatchBuilder[dict[str, Any]](
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
        )

        self.dq_service = DQExecutionService(
            DQEngine()
        )

    def add_record(
        self,
        record: dict[str, Any],
    ) -> list[DQBatchResult]:
        """
        Add one record and process any completed batch.
        """

        batches = self.batch_builder.add(record)

        results: list[DQBatchResult] = []

        for batch in batches:
            results.append(
                self.dq_service.evaluate_batch(
                    batch,
                    self.rule_set,
                )
            )

        return results

    def flush(self) -> DQBatchResult | None:
        """
        Process the current partial batch.
        """

        batch = self.batch_builder.flush()

        if not batch:
            return None

        return self.dq_service.evaluate_batch(
            batch,
            self.rule_set,
        )