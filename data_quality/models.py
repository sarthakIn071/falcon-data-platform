from uuid import UUID

from pydantic import BaseModel


class DQExecutionContext(BaseModel):
    """
    Identifies the pipeline execution and DQ step
    associated with a batch.
    """

    pipeline_id: int
    run_id: UUID
    step_id: int