
import json
from itertools import chain
from typing import Any, Iterator, IO

import ijson
from ijson.common import JSONError

from parsers.base import BaseParser
from parsers.exceptions import ParsingError
from parsers.models import ParserConfig


class JSONParser(BaseParser):
    """
    Parser for JSON payloads.

    Supports:
    - JSON bytes, strings, dictionaries and lists.
    - Standard JSON document parsing.
    - Streaming JSON arrays using ijson.
    - Nested JSON arrays using record_path.
    - NDJSON streaming, one record per line.
    """

    format_name = "JSON"

    def parse(
        self,
        payload: bytes | str | dict | list,
        config: ParserConfig | None = None,
    ) -> list[dict[str, Any]]:

        if config is None:
            config = ParserConfig(format="JSON")

        if config.format != self.format_name:
            raise ParsingError(
                f"Invalid parser configuration: expected JSON, got {config.format}",
                format_name=self.format_name,
            )

        encoding = config.encoding

        try:
            if isinstance(payload, bytes):
                payload = payload.decode(encoding)

            if isinstance(payload, str):
                data = json.loads(payload)

            elif isinstance(payload, (dict, list)):
                data = payload

            else:
                raise ParsingError(
                    "Unsupported JSON payload type",
                    format_name=self.format_name,
                )

            if config.record_path:
                data = self._extract_record_path(
                    data,
                    config.record_path
                )

            if isinstance(data, dict):
                return [data]

            if isinstance(data, list):
                if not all(isinstance(record, dict) for record in data):
                    raise ParsingError(
                        "JSON array must contain only objects",
                        format_name=self.format_name,
                    )

                return data

            raise ParsingError(
                "JSON payload must contain an object or array of objects",
                format_name=self.format_name,
            )

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ParsingError(
                f"Invalid JSON payload: {exc}",
                format_name=self.format_name,
            ) from exc

    def parse_stream(
        self,
        stream: IO[bytes],
        config: ParserConfig | None = None,
    ) -> Iterator[dict[str, Any]]:
        """
        Parse a binary stream incrementally.

        Supports standard JSON documents and NDJSON.

        Yields one dictionary at a time.
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
    ) -> Iterator[dict[str, Any]]:
        """
        Parse NDJSON incrementally.

        Each non-empty line must contain one JSON object.
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

            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ParsingError(
                    f"Invalid JSON on line {line_number}: {exc}",
                    format_name=self.format_name,
                ) from exc

            if not isinstance(record, dict):
                raise ParsingError(
                    f"JSON line {line_number} must contain an object",
                    format_name=self.format_name,
                )

            yield record

    def _parse_json_document(
        self,
        stream: IO[bytes],
        config: ParserConfig,
    ) -> Iterator[dict[str, Any]]:
        """
        Parse a JSON document incrementally using ijson.

        Supports:
        - Root JSON arrays.
        - Root JSON objects.
        - Nested arrays selected using record_path.
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

            for record in records:

                if not isinstance(record, dict):
                    raise ParsingError(
                        "JSON array must contain only objects",
                        format_name=self.format_name,
                    )

                yield record

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
