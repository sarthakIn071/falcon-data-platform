from datetime import datetime, timezone
from typing import Any

from data_quality.models import DQExecutionContext
from data_quality.rules import DQRuleSet
from metadata.repository import PipelineStepRunRepository
from processing.dq_processor import DQBatchProcessor


class DQExecutionCoordinator:
    """
    Coordinates DQ batch execution and execution metadata persistence.
    """

    def __init__(
        self,
        processor: DQBatchProcessor,
        repository: PipelineStepRunRepository,
        context: DQExecutionContext,
    ):
        self.processor = processor
        self.repository = repository
        self.context = context

    def execute_batch(
        self,
        records: list[dict[str, Any]],
    ):
        start_time = datetime.now(timezone.utc)

        step_run_id = self.repository.create_step_run(
            run_id=self.context.run_id,
            step_id=self.context.step_id,
            status="RUNNING",
            start_time=start_time,
        )

        try:
            batch_result = self.processor.dq_service.evaluate_batch(
                records,
                self.processor.rule_set,
            )

            status = (
                "COMPLETED"
                if batch_result.error_count == 0
                else "FAILED"
            )

            self.repository.finalize_step_run(
                step_run_id=step_run_id,
                status=status,
                end_time=datetime.now(timezone.utc),
                input_count=batch_result.total_records,
                output_count=batch_result.passed_records,
                error_count=batch_result.error_count,
            )

            return batch_result

        except Exception as exc:
            self.repository.finalize_step_run(
                step_run_id=step_run_id,
                status="FAILED",
                end_time=datetime.now(timezone.utc),
                input_count=len(records),
                output_count=0,
                error_count=len(records),
            )
            raise exc