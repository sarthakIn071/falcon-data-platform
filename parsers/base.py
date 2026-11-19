from abc import ABC, abstractmethod
from typing import Any, Iterator, IO

from parsers.models import ParserConfig


class BaseParser(ABC):
    """
    Common interface for all Falcon data format parsers.
    """

    format_name: str

    @abstractmethod
    def parse(
        self,
        payload: bytes | str | dict | list,
        config: ParserConfig | None = None,
    ) -> list[dict[str, Any]]:
        """
        Parse a raw payload into a list of normalized records.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_stream(
        self,
        stream: IO[bytes],
        config: ParserConfig | None = None,
    ) -> Iterator[dict[str, Any]]:
        """
        Parse a binary stream incrementally.

        Yields one normalized record at a time.
        """
        raise NotImplementedError