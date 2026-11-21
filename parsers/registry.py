
from typing import Type

from parsers.base import BaseParser
from parsers.json_parser import JSONParser
from parsers.avro_parser import AvroParser


class ParserRegistry:
    """
    Registry for Falcon data format parsers.

    Maps a format such as JSON, AVRO, CSV, etc.
    to its parser implementation.
    """

    _parsers: dict[str, Type[BaseParser]] = {}

    @classmethod
    def register(
        cls,
        format_name: str,
        parser_class: Type[BaseParser],
    ) -> None:
        """
        Register a parser implementation.
        """

        format_name = format_name.upper()

        if format_name in cls._parsers:
            raise ValueError(
                f"Parser already registered: {format_name}"
            )

        cls._parsers[format_name] = parser_class

    @classmethod
    def get(cls, format_name: str) -> Type[BaseParser]:
        """
        Retrieve a parser class by format.
        """

        format_name = format_name.upper()

        parser_class = cls._parsers.get(format_name)

        if parser_class is None:
            raise ValueError(
                f"Parser not registered: {format_name}"
            )

        return parser_class

    @classmethod
    def list_parsers(cls) -> list[str]:
        """
        Return all registered parser formats.
        """

        return sorted(cls._parsers.keys())


# Register built-in parsers
# Register built-in parsers
ParserRegistry.register("JSON", JSONParser)
ParserRegistry.register("AVRO", AvroParser)
