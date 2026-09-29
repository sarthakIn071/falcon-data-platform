from datetime import datetime, timezone
from uuid import uuid4

from config.settings import settings
from metadata.repository import PipelineStepRunRepository


def test_create_step_run():
    repository = PipelineStepRunRepository(
        settings.database_url
    )

    run_id = uuid4()

    with repository._connect() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO falcon_metadata.sources (
                    source_name,
                    source_type
                )
                VALUES (%s, %s)
                RETURNING source_id
                """,
                (
                    f"test-source-{run_id}",
                    "TEST",
                ),
            )
            source_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.targets (
                    target_name,
                    target_type
                )
                VALUES (%s, %s)
                RETURNING target_id
                """,
                (
                    f"test-target-{run_id}",
                    "TEST",
                ),
            )
            target_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.pipelines (
                    pipeline_name,
                    source_id,
                    target_id,
                    ingestion_mode,
                    transport_type
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING pipeline_id
                """,
                (
                    f"test-pipeline-{run_id}",
                    source_id,
                    target_id,
                    "BATCH",
                    "KAFKA",
                ),
            )
            pipeline_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.pipeline_steps (
                    pipeline_id,
                    step_name,
                    step_type,
                    step_order
                )
                VALUES (%s, %s, %s, %s)
                RETURNING step_id
                """,
                (
                    pipeline_id,
                    "DQ Test",
                    "DATA_QUALITY",
                    1,
                ),
            )
            step_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.pipeline_runs (
                    run_id,
                    pipeline_id,
                    status
                )
                VALUES (%s, %s, %s)
                """,
                (
                    run_id,
                    pipeline_id,
                    "RUNNING",
                ),
            )

        connection.commit()

def test_finalize_step_run():
    repository = PipelineStepRunRepository(
        settings.database_url
    )

    run_id = uuid4()

    with repository._connect() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO falcon_metadata.sources (
                    source_name,
                    source_type
                )
                VALUES (%s, %s)
                RETURNING source_id
                """,
                (
                    f"test-source-{run_id}",
                    "TEST",
                ),
            )
            source_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.targets (
                    target_name,
                    target_type
                )
                VALUES (%s, %s)
                RETURNING target_id
                """,
                (
                    f"test-target-{run_id}",
                    "TEST",
                ),
            )
            target_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.pipelines (
                    pipeline_name,
                    source_id,
                    target_id,
                    ingestion_mode,
                    transport_type
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING pipeline_id
                """,
                (
                    f"test-pipeline-{run_id}",
                    source_id,
                    target_id,
                    "BATCH",
                    "KAFKA",
                ),
            )
            pipeline_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.pipeline_steps (
                    pipeline_id,
                    step_name,
                    step_type,
                    step_order
                )
                VALUES (%s, %s, %s, %s)
                RETURNING step_id
                """,
                (
                    pipeline_id,
                    "DQ Test",
                    "DATA_QUALITY",
                    1,
                ),
            )
            step_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO falcon_metadata.pipeline_runs (
                    run_id,
                    pipeline_id,
                    status
                )
                VALUES (%s, %s, %s)
                """,
                (
                    run_id,
                    pipeline_id,
                    "RUNNING",
                ),
            )

        connection.commit()

    try:
        start_time = datetime.now(timezone.utc)

        step_run_id = repository.create_step_run(
            run_id=run_id,
            step_id=step_id,
            status="RUNNING",
            start_time=start_time,
        )

        end_time = datetime.now(timezone.utc)

        repository.finalize_step_run(
            step_run_id=step_run_id,
            status="FAILED",
            end_time=end_time,
            input_count=1000,
            output_count=930,
            error_count=70,
        )

        with repository._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        status,
                        end_time,
                        input_count,
                        output_count,
                        error_count
                    FROM falcon_metadata.pipeline_step_runs
                    WHERE step_run_id = %s
                    """,
                    (step_run_id,),
                )

                row = cursor.fetchone()

        assert row is not None
        assert row[0] == "FAILED"
        assert row[1] is not None
        assert row[2] == 1000
        assert row[3] == 930
        assert row[4] == 70

    finally:
        with repository._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM falcon_metadata.pipeline_step_runs
                    WHERE run_id = %s
                    """,
                    (run_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM falcon_metadata.pipeline_runs
                    WHERE run_id = %s
                    """,
                    (run_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM falcon_metadata.pipeline_steps
                    WHERE step_id = %s
                    """,
                    (step_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM falcon_metadata.pipelines
                    WHERE pipeline_id = %s
                    """,
                    (pipeline_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM falcon_metadata.sources
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM falcon_metadata.targets
                    WHERE target_id = %s
                    """,
                    (target_id,),
                )

            connection.commit()