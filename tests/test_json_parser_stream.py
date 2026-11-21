
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

    results = list(parser.parse_stream(BytesIO(payload)))

    assert len(results) == 3
    assert all(result.success for result in results)

    assert results[0].record["name"] == "John"
    assert results[2].record["name"] == "Peter"

    assert [result.record_number for result in results] == [1, 2, 3]


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

    results = list(parser.parse_stream(BytesIO(payload), config))

    assert len(results) == 2
    assert results[0].record["name"] == "John"
    assert all(result.success for result in results)


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

    results = list(parser.parse_stream(BytesIO(payload), config))

    assert len(results) == 3
    assert results[1].record["name"] == "David"
    assert all(result.success for result in results)


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

    results = list(parser.parse_stream(BytesIO(payload), config))

    assert len(results) == 2
    assert results[0].record["id"] == 1
    assert results[1].record["id"] == 2


def test_stream_empty_array(parser):
    payload = b"[]"

    results = list(parser.parse_stream(BytesIO(payload)))

    assert results == []


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
        b'{"id": 3}\n'
    )

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    results = list(parser.parse_stream(BytesIO(payload), config))

    assert len(results) == 3

    assert results[0].success is True
    assert results[0].record == {"id": 1}
    assert results[0].record_number == 1

    assert results[1].success is False
    assert results[1].record is None
    assert results[1].record_number == 2
    assert "line 2" in results[1].error

    assert results[2].success is True
    assert results[2].record == {"id": 3}
    assert results[2].record_number == 3


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

    results = parser.parse_stream(BytesIO(payload))

    assert iter(results) is results

    first = next(results)
    second = next(results)

    assert first.success is True
    assert first.record == {"id": 1}
    assert first.record_number == 1

    assert second.success is True
    assert second.record == {"id": 2}
    assert second.record_number == 2
