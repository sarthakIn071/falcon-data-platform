
from collections.abc import Iterable, Iterator
from typing import Any

from parsers.results import ParseResult
from processing.results import RecordProcessingResult
from validation.service import ValidationService


class RecordProcessor:
    """
    Coordinates parsing outcomes with validation and quarantine.

    It does not implement parsing, validation rules, or persistence.
    Those responsibilities remain with their respective components.
    """

    def __init__(
        self,
        validation_service: ValidationService,
        run_id: str,
        pipeline_id: int | None = None,
        entity: str | None = None,
        source_type: str | None = None,
        source_name: str | None = None,
        file_name: str | None = None,
        file_path: str | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self.validation_service = validation_service
        self.run_id = run_id
        self.pipeline_id = pipeline_id
        self.entity = entity
        self.source_type = source_type
        self.source_name = source_name
        self.file_name = file_name
        self.file_path = file_path
        self.encoding = encoding

    def process(
        self,
        parse_results: Iterable[ParseResult],
    ) -> Iterator[RecordProcessingResult]:
        """
        Validate successfully parsed records and quarantine parse failures.
        """

        for parse_result in parse_results:

            if not parse_result.success:
                if parse_result.error is None:
                    raise ValueError(
                        "Failed ParseResult must contain an error"
                    )

                quarantine_reference = (
                    self.validation_service.quarantine_parse_error(
                        raw_data=parse_result.raw_data,
                        record_number=parse_result.record_number,
                        error=parse_result.error,
                        run_id=self.run_id,
                        pipeline_id=self.pipeline_id,
                        entity=self.entity,
                        source_type=self.source_type,
                        source_name=self.source_name,
                        file_name=self.file_name,
                        file_path=self.file_path,
                        encoding=self.encoding,
                    )
                )

                yield RecordProcessingResult(
                    record_number=parse_result.record_number,
                    status="PARSING_FAILED",
                    quarantine_reference=quarantine_reference,
                    error=parse_result.error,
                )

                continue

            if parse_result.record is None:
                raise ValueError(
                    "Successful ParseResult must contain a record"
                )

            validation_result = (
                self.validation_service.validate_record(
                    record=parse_result.record,
                    run_id=self.run_id,
                    pipeline_id=self.pipeline_id,
                    entity=self.entity,
                    source_type=self.source_type,
                    source_name=self.source_name,
                )
            )

            yield RecordProcessingResult(
                record_number=parse_result.record_number,
                status=(
                    "SUCCESS"
                    if validation_result.valid
                    else "VALIDATION_FAILED"
                ),
                validation_result=validation_result,
            )
