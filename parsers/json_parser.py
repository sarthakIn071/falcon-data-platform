
import json
from io import BytesIO
from itertools import chain
from typing import Any, Iterator, IO

import ijson
from ijson.common import JSONError

from parsers.base import BaseParser
from parsers.exceptions import ParsingError
from parsers.models import ParserConfig
from parsers.results import ParseResult


class JSONParser(BaseParser):
    """
    Parser for JSON payloads.

    Supports:
    - JSON bytes, strings, dictionaries and lists.
    - Standard JSON document parsing.
    - Streaming JSON arrays using ijson.
    - Nested JSON arrays using record_path.
    - NDJSON streaming, one record per line.
    - Record-level error recovery in NDJSON mode.
    """

    format_name = "JSON"

    def parse(
        self,
        payload: bytes | str | dict | list,
        config: ParserConfig | None = None,
    ) -> list[ParseResult]:

        if config is None:
            config = ParserConfig(format="JSON")

        if config.format != self.format_name:
            raise ParsingError(
                f"Invalid parser configuration: expected JSON, got {config.format}",
                format_name=self.format_name,
            )

        # NDJSON is handled through the common streaming interface.
        if config.json_mode == "LINES":
            if isinstance(payload, (dict, list)):
                raise ParsingError(
                    "NDJSON mode requires a string or binary payload",
                    format_name=self.format_name,
                )

            if isinstance(payload, str):
                try:
                    payload = payload.encode(config.encoding)
                except UnicodeEncodeError as exc:
                    raise ParsingError(
                        f"Unable to encode JSON payload: {exc}",
                        format_name=self.format_name,
                    ) from exc

            if not isinstance(payload, bytes):
                raise ParsingError(
                    "Unsupported JSON payload type",
                    format_name=self.format_name,
                )

            return list(self.parse_stream(BytesIO(payload), config))

        # Decode and parse an in-memory JSON document.
        try:
            if isinstance(payload, bytes):
                data = payload.decode(config.encoding)

            elif isinstance(payload, str):
                data = payload

            elif isinstance(payload, (dict, list)):
                data = payload

            else:
                raise ParsingError(
                    "Unsupported JSON payload type",
                    format_name=self.format_name,
                )

            if isinstance(data, str):
                data = json.loads(data)

            if config.record_path:
                data = self._extract_record_path(
                    data,
                    config.record_path,
                )

            if isinstance(data, dict):
                records = [data]

            elif isinstance(data, list):
                records = data

            else:
                raise ParsingError(
                    "JSON payload must contain an object or array of objects",
                    format_name=self.format_name,
                )

            results = []

            for record_number, record in enumerate(records, start=1):
                if not isinstance(record, dict):
                    raise ParsingError(
                        "JSON array must contain only objects",
                        format_name=self.format_name,
                    )

                results.append(
                    ParseResult(
                        record=record,
                        record_number=record_number,
                    )
                )

            return results

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ParsingError(
                f"Invalid JSON payload: {exc}",
                format_name=self.format_name,
            ) from exc


    def parse_stream(
        self,
        stream: IO[bytes],
        config: ParserConfig | None = None,
    ) -> Iterator[ParseResult]:
        """
        Parse a binary stream incrementally.

        Supports standard JSON documents and NDJSON.

        Yields ParseResult objects.
        The caller owns the stream and must close it.
        """

        if config is None:
            config = ParserConfig(format="JSON")

        if config.format != self.format_name:
            raise ParsingError(
                f"Invalid parser configuration: expected JSON, got {config.format}",
                format_name=self.format_name,
            )

        if config.json_mode == "LINES":
            yield from self._parse_json_lines(stream, config)
            return

        yield from self._parse_json_document(stream, config)

    def _parse_json_lines(
        self,
        stream: IO[bytes],
        config: ParserConfig,
    ) -> Iterator[ParseResult]:
        """
        Parse NDJSON incrementally.

        Each non-empty line produces one ParseResult.
        Invalid lines produce failed ParseResult objects.
        Processing continues after individual line failures.
        """

        if config.record_path:
            raise ParsingError(
                "record_path is not supported in LINES mode",
                format_name=self.format_name,
            )

        for line_number, raw_line in enumerate(stream, start=1):

            if not raw_line.strip():
                continue

            try:
                line = raw_line.decode(config.encoding)
                record = json.loads(line)

                if not isinstance(record, dict):
                    raise ValueError(
                        "JSON line must contain an object"
                    )

                yield ParseResult(
                    record=record,
                    record_number=line_number,
                    raw_data=raw_line,
                )

            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                ValueError,
            ) as exc:

                yield ParseResult(
                    record=None,
                    record_number=line_number,
                    raw_data=raw_line,
                    error=f"Invalid JSON on line {line_number}: {exc}",
                )

    def _parse_json_document(
        self,
        stream: IO[bytes],
        config: ParserConfig,
    ) -> Iterator[ParseResult]:
        """
        Parse a JSON document incrementally using ijson.

        Supports:
        - Root JSON arrays.
        - Root JSON objects.
        - Nested arrays selected using record_path.

        A malformed document raises ParsingError because
        individual records cannot always be recovered safely.
        """

        events = ijson.parse(stream)

        try:
            first_event = next(events, None)

            if first_event is None:
                raise ParsingError(
                    "Empty JSON document",
                    format_name=self.format_name,
                )

            if config.record_path:

                if not config.record_path.startswith("$."):
                    raise ParsingError(
                        f"Unsupported record_path: {config.record_path}",
                        format_name=self.format_name,
                    )

                target_path = config.record_path[2:]

                if not target_path:
                    raise ParsingError(
                        f"Unsupported record_path: {config.record_path}",
                        format_name=self.format_name,
                    )

                prefix = f"{target_path}.item"

            elif first_event[1] == "start_array":
                prefix = "item"
                target_path = None

            elif first_event[1] == "start_map":
                prefix = ""
                target_path = None

            else:
                raise ParsingError(
                    "JSON document must contain an object or array of objects",
                    format_name=self.format_name,
                )

            found_target_array = False

            def tracked_events():
                nonlocal found_target_array

                for event in chain((first_event,), events):

                    if (
                        target_path is not None
                        and event[0] == target_path
                        and event[1] == "start_array"
                    ):
                        found_target_array = True

                    yield event

            records = ijson.items(
                tracked_events(),
                prefix,
            )

            for record_number, record in enumerate(records, start=1):

                if not isinstance(record, dict):
                    raise ParsingError(
                        "JSON array must contain only objects",
                        format_name=self.format_name,
                    )

                yield ParseResult(
                    record=record,
                    record_number=record_number,
                )

            if target_path is not None and not found_target_array:
                raise ParsingError(
                    f"record_path not found or does not reference an array: {config.record_path}",
                    format_name=self.format_name,
                )

        except JSONError as exc:
            raise ParsingError(
                f"Invalid JSON stream: {exc}",
                format_name=self.format_name,
            ) from exc

    def _extract_record_path(
        self,
        data: Any,
        record_path: str,
    ) -> Any:
        """
        Extract nested data using simple JSON paths.

        Supported examples:
        $.customers
        $.data.customers
        """

        if not record_path.startswith("$."):
            raise ParsingError(
                f"Unsupported record_path: {record_path}",
                format_name=self.format_name,
            )

        path_parts = record_path[2:].split(".")

        current = data

        for part in path_parts:

            if not isinstance(current, dict) or part not in current:
                raise ParsingError(
                    f"record_path not found: {record_path}",
                    format_name=self.format_name,
                )

            current = current[part]

        return current
