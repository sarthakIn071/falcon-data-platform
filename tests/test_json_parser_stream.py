
from io import BytesIO

import pytest

from parsers.json_parser import JSONParser
from parsers.exceptions import ParsingError
from parsers.models import ParserConfig


@pytest.fixture
def parser():
    return JSONParser()


def test_stream_json_array(parser):
    payload = b"""
    [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "David"},
        {"id": 3, "name": "Peter"}
    ]
    """

    records = list(parser.parse_stream(BytesIO(payload)))

    assert len(records) == 3
    assert records[0]["name"] == "John"
    assert records[2]["name"] == "Peter"


def test_stream_nested_json_array(parser):
    payload = b"""
    {
        "data": {
            "customers": [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "David"}
            ]
        }
    }
    """

    config = ParserConfig(
        format="JSON",
        record_path="$.data.customers",
    )

    records = list(
        parser.parse_stream(BytesIO(payload), config)
    )

    assert len(records) == 2
    assert records[0]["name"] == "John"


def test_stream_ndjson(parser):
    payload = (
        b'{"id": 1, "name": "John"}\n'
        b'{"id": 2, "name": "David"}\n'
        b'{"id": 3, "name": "Peter"}\n'
    )

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    records = list(
        parser.parse_stream(BytesIO(payload), config)
    )

    assert len(records) == 3
    assert records[1]["name"] == "David"


def test_stream_ndjson_skips_blank_lines(parser):
    payload = (
        b'{"id": 1}\n'
        b'\n'
        b'{"id": 2}\n'
    )

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    records = list(
        parser.parse_stream(BytesIO(payload), config)
    )

    assert len(records) == 2


def test_stream_empty_array(parser):
    payload = b"[]"

    records = list(
        parser.parse_stream(BytesIO(payload))
    )

    assert records == []


def test_stream_invalid_json(parser):
    payload = b'[{"id": 1}, invalid]'

    with pytest.raises(ParsingError):
        list(parser.parse_stream(BytesIO(payload)))


def test_stream_non_object_record(parser):
    payload = b'[{"id": 1}, 123]'

    with pytest.raises(ParsingError):
        list(parser.parse_stream(BytesIO(payload)))


def test_stream_missing_record_path(parser):
    payload = b'{"data": {"orders": []}}'

    config = ParserConfig(
        format="JSON",
        record_path="$.data.customers",
    )

    with pytest.raises(ParsingError):
        list(parser.parse_stream(BytesIO(payload), config))


def test_stream_invalid_ndjson(parser):
    payload = (
        b'{"id": 1}\n'
        b'invalid-json\n'
    )

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    with pytest.raises(ParsingError, match="line 2"):
        list(parser.parse_stream(BytesIO(payload), config))


def test_stream_ndjson_rejects_record_path(parser):
    payload = b'{"id": 1}\n'

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
        record_path="$.customers",
    )

    with pytest.raises(ParsingError):
        list(parser.parse_stream(BytesIO(payload), config))


def test_stream_yields_iterator(parser):
    payload = b'[{"id": 1}, {"id": 2}]'

    records = parser.parse_stream(BytesIO(payload))

    assert iter(records) is records
    assert next(records) == {"id": 1}
    assert next(records) == {"id": 2}
