
from io import BytesIO

from parsers.json_parser import JSONParser
from parsers.models import ParserConfig


def test_stream_continues_after_invalid_line():
    parser = JSONParser()

    payload = (
        b'{"id": 1}\n'
        b'{"id": 2}\n'
        b'invalid-json\n'
        b'{"id": 4}\n'
    )

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    results = list(
        parser.parse_stream(BytesIO(payload), config)
    )

    assert len(results) == 4

    assert results[0].success is True
    assert results[0].record == {"id": 1}
    assert results[0].record_number == 1

    assert results[1].success is True
    assert results[1].record == {"id": 2}
    assert results[1].record_number == 2

    assert results[2].success is False
    assert results[2].record is None
    assert results[2].record_number == 3
    assert results[2].raw_data == b"invalid-json\n"
    assert "line 3" in results[2].error

    assert results[3].success is True
    assert results[3].record == {"id": 4}
    assert results[3].record_number == 4


def test_stream_recovery_preserves_raw_data():
    parser = JSONParser()

    payload = b'{"id": 10}\n'

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    result = next(
        parser.parse_stream(BytesIO(payload), config)
    )

    assert result.success is True
    assert result.record == {"id": 10}
    assert result.raw_data == payload
    assert result.record_number == 1


def test_stream_document_mode_returns_parse_results():
    parser = JSONParser()

    config = ParserConfig(
        format="JSON",
        json_mode="DOCUMENT",
    )

    results = list(
        parser.parse_stream(
            BytesIO(b'[{"id": 1}, {"id": 2}]'),
            config,
        )
    )

    assert len(results) == 2

    assert results[0].success is True
    assert results[0].record == {"id": 1}
    assert results[0].record_number == 1

    assert results[1].success is True
    assert results[1].record == {"id": 2}
    assert results[1].record_number == 2


def test_stream_recovery_handles_non_object_json():
    parser = JSONParser()

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    results = list(
        parser.parse_stream(
            BytesIO(b'{"id": 1}\n123\n{"id": 3}\n'),
            config,
        )
    )

    assert len(results) == 3

    assert results[0].success is True
    assert results[0].record == {"id": 1}

    assert results[1].success is False
    assert results[1].record is None
    assert results[1].record_number == 2

    assert results[2].success is True
    assert results[2].record == {"id": 3}


def test_stream_recovery_skips_blank_lines():
    parser = JSONParser()

    config = ParserConfig(
        format="JSON",
        json_mode="LINES",
    )

    results = list(
        parser.parse_stream(
            BytesIO(b'{"id": 1}\n\n{"id": 2}\n'),
            config,
        )
    )

    assert len(results) == 2

    assert results[0].record == {"id": 1}
    assert results[0].record_number == 1

    assert results[1].record == {"id": 2}
    assert results[1].record_number == 3
