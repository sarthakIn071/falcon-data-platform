
from io import BytesIO
from typing import IO, Iterator

from fastavro import reader

from parsers.base import BaseParser
from parsers.exceptions import ParsingError
from parsers.models import ParserConfig
from parsers.results import ParseResult


class AvroParser(BaseParser):
    """
    Parser for Avro Object Container Files (OCF).

    Uses the schema embedded in the Avro file as the writer schema
    and the configured inline schema as the reader schema.
    """

    format_name = "AVRO"

    def parse(
        self,
        payload: bytes | str | dict | list,
        config: ParserConfig | None = None,
    ) -> list[ParseResult]:
        """
        Parse an in-memory Avro payload.
        """

        if config is None:
            raise ParsingError(
                "Avro parsing requires an explicit ParserConfig",
                format_name=self.format_name,
            )

        if not isinstance(payload, bytes):
            raise ParsingError(
                "Avro payload must be binary bytes",
                format_name=self.format_name,
            )

        stream = BytesIO(payload)

        return list(self.parse_stream(stream, config))

    def parse_stream(
        self,
        stream: IO[bytes],
        config: ParserConfig | None = None,
    ) -> Iterator[ParseResult]:
        """
        Read Avro OCF records incrementally.

        The caller owns the stream and must close it.
        """

        if config is None:
            raise ParsingError(
                "Avro parsing requires an explicit ParserConfig",
                format_name=self.format_name,
            )

        if config.format != self.format_name:
            raise ParsingError(
                f"Invalid parser configuration: expected AVRO, got {config.format}",
                format_name=self.format_name,
            )

        if not config.avro_schema:
            raise ParsingError(
                "An inline Avro reader schema is required",
                format_name=self.format_name,
            )

        try:
            avro_reader = reader(
                stream,
                reader_schema=config.avro_schema,
            )

            for record_number, record in enumerate(avro_reader, start=1):

                if not isinstance(record, dict):
                    raise ParsingError(
                        "Avro record must be a dictionary",
                        format_name=self.format_name,
                    )

                yield ParseResult(
                    record=record,
                    record_number=record_number,
                )

        except ParsingError:
            raise

        except Exception as exc:
            raise ParsingError(
                f"Failed to parse Avro stream: {exc}",
                format_name=self.format_name,
            ) from exc
