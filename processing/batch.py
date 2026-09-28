from time import monotonic
from typing import Generic, TypeVar

T = TypeVar("T")


class BatchBuilder(Generic[T]):
    """
    Collects records into batches based on batch size or timeout.
    """

    def __init__(
        self,
        batch_size: int,
        timeout_seconds: float = 30.0,
    ):
        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero"
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero"
            )

        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds

        self._records: list[T] = []
        self._batch_started_at: float | None = None

    def add(self, record: T) -> list[list[T]]:
        """
        Add one record.

        Returns a completed batch when batch_size is reached.
        """
        if not self._records:
            self._batch_started_at = monotonic()

        self._records.append(record)

        if len(self._records) >= self.batch_size:
            return [self.flush()]

        return []

    def flush(self) -> list[T]:
        """
        Return the current batch and reset the builder.
        """
        batch = self._records

        self._records = []
        self._batch_started_at = None

        return batch

    def size(self) -> int:
        """
        Return the number of records currently buffered.
        """
        return len(self._records)

    def is_timeout_expired(self) -> bool:
        """
        Return True when the current batch has exceeded its timeout.
        """
        if not self._records:
            return False

        if self._batch_started_at is None:
            return False

        elapsed = monotonic() - self._batch_started_at

        return elapsed >= self.timeout_seconds