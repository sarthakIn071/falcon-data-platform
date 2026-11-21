from abc import ABC, abstractmethod
from typing import Iterator, IO

from parsers.models import ParserConfig
from parsers.results import ParseResult


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
    ) -> list[ParseResult]:
        """
        Parse an in-memory payload.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_stream(
        self,
        stream: IO[bytes],
        config: ParserConfig | None = None,
    ) -> Iterator[ParseResult]:
        """
        Parse a stream incrementally.
        """
        raise NotImplementedError