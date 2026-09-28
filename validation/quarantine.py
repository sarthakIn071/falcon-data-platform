import json
from pathlib import Path

from validation.exceptions import QuarantineError
from validation.models import QuarantineRecord


class QuarantineStore:
    """
    Stores quarantined records and files on the local filesystem.
    """

    def __init__(self, base_path: str = "quarantine"):
        self.base_path = Path(base_path)

    def quarantine_record(self, record: QuarantineRecord) -> str:
        """
        Save a quarantined record as a JSON file.
        """

        try:
            run_path = self.base_path / "records" / record.run_id
            run_path.mkdir(parents=True, exist_ok=True)

            file_path = run_path / f"{record.quarantine_id}.json"

            with file_path.open("w", encoding="utf-8") as file:
                json.dump(
                    record.model_dump(mode="json"),
                    file,
                    indent=2,
                )

            return str(file_path)

        except OSError as exc:
            raise QuarantineError(
                f"Failed to quarantine record: {exc}"
            ) from exc

    def quarantine_file(
        self,
        source_file: str,
        quarantine_record: QuarantineRecord,
    ) -> str:
        """
        Copy the original file and quarantine metadata
        into the quarantine area.
        """

        try:
            source_path = Path(source_file)

            if not source_path.exists():
                raise QuarantineError(
                    f"Source file does not exist: {source_file}"
                )

            run_path = self.base_path / "files" / quarantine_record.run_id
            run_path.mkdir(parents=True, exist_ok=True)

            # Copy original file
            destination_path = run_path / source_path.name

            destination_path.write_bytes(
                source_path.read_bytes()
            )

            # Save quarantine metadata
            metadata_path = run_path / "quarantine.json"

            with metadata_path.open("w", encoding="utf-8") as file:
                json.dump(
                    quarantine_record.model_dump(mode="json"),
                    file,
                    indent=2,
                )

            return str(destination_path)

        except OSError as exc:
            raise QuarantineError(
                f"Failed to quarantine file: {exc}"
            ) from exc