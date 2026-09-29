import psycopg
from datetime import datetime
from uuid import UUID


class PipelineStepRunRepository:
    """
    Persists pipeline step execution information.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _connect(self):
        return psycopg.connect(self.connection_string)

    def create_step_run(
        self,
        run_id: UUID,
        step_id: int,
        status: str,
        start_time: datetime,
    ) -> int:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO falcon_metadata.pipeline_step_runs (
                        run_id,
                        step_id,
                        status,
                        start_time
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING step_run_id
                    """,
                    (
                        run_id,
                        step_id,
                        status,
                        start_time,
                    ),
                )

                step_run_id = cursor.fetchone()[0]

            connection.commit()
            
        return step_run_id

    def finalize_step_run(
    self,
    step_run_id: int,
    status: str,
    end_time: datetime,
    input_count: int,
    output_count: int,
    error_count: int,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE falcon_metadata.pipeline_step_runs
                    SET
                        status = %s,
                        end_time = %s,
                        input_count = %s,
                        output_count = %s,
                        error_count = %s
                    WHERE step_run_id = %s
                    """,
                    (
                        status,
                        end_time,
                        input_count,
                        output_count,
                        error_count,
                        step_run_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"Pipeline step run not found: {step_run_id}"
                    )

            connection.commit()

        return step_run_id