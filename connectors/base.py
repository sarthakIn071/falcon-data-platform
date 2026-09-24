from abc import ABC, abstractmethod
from typing import Iterator

from messaging.event import FalconEvent


class BaseConnector(ABC):
    """
    Base interface for all Falcon source connectors.

    Every connector is responsible for:
    1. Connecting to a source
    2. Extracting records
    3. Converting records into FalconEvents
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def connect(self) -> None:
        """Establish connection with the source."""
        pass

    @abstractmethod
    def extract(self) -> Iterator[dict]:
        """Extract records from the source."""
        pass

    @abstractmethod
    def to_event(self, record: dict) -> FalconEvent:
        """Convert a source record into a FalconEvent."""
        pass

    def run(self) -> Iterator[FalconEvent]:
        """
        Execute the standard connector flow.
        """
        self.connect()

        for record in self.extract():
            yield self.to_event(record)

    def close(self) -> None:
        """Close the source connection."""
        pass