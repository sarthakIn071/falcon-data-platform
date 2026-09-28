from typing import Any
from uuid import uuid4
from messaging.event import FalconEvent

from validation.models import QuarantineRecord, ValidationResult
from validation.quarantine import QuarantineStore
from validation.validator import SchemaValidator


class ValidationService:
    """
    Coordinates validation and quarantine for records.
    """

    def __init__(
        self,
        validator: SchemaValidator,
        quarantine_store: QuarantineStore,
    ):
        self.validator = validator
        self.quarantine_store = quarantine_store

    def validate_record(
        self,
        record: dict[str, Any],
        run_id: str,
        pipeline_id: int | None = None,
        event_id: str | None = None,
        entity: str | None = None,
        source_type: str | None = None,
        source_name: str | None = None,
    ) -> ValidationResult:

        result = self.validator.validate(record)

        if result.valid:
            return result

        quarantine_record = QuarantineRecord(
            quarantine_id=str(uuid4()),
            quarantine_type="RECORD",
            event_id=event_id,
            run_id=run_id,
            pipeline_id=pipeline_id,
            entity=entity,
            source_type=source_type,
            source_name=source_name,
            reason="Schema validation failed",
            errors=result.errors,
            original_data=record,
        )

        self.quarantine_store.quarantine_record(quarantine_record)

        return result

    def validate_event(self, event: FalconEvent) -> ValidationResult:
        """
        Validate a FalconEvent payload and quarantine the event
        when validation fails.
        """

        result = self.validator.validate(event.payload)

        if result.valid:
            return result

        quarantine_record = QuarantineRecord(
            quarantine_id=str(uuid4()),
            quarantine_type="RECORD",
            event_id=event.event_id,
            run_id=event.run_id,
            entity=event.entity,
            source_type=event.source.type,
            source_name=event.source.connector,
            reason="Schema validation failed",
            errors=result.errors,
            original_data=event.model_dump(mode="json"),
        )

        self.quarantine_store.quarantine_record(quarantine_record)

        return result