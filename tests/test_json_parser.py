
import pytest

from parsers.json_parser import JSONParser
from parsers.exceptions import ParsingError
from parsers.models import ParserConfig


def test_parse_json_object():
    parser = JSONParser()

    payload = {
        "customer_id": 101,
        "name": "John"
    }

    result = parser.parse(payload)

    assert len(result) == 1
    assert result[0].record == {
        "customer_id": 101,
        "name": "John"
    }
    assert result[0].record_number == 1
    assert result[0].success is True


def test_parse_json_string():
    parser = JSONParser()

    payload = '{"customer_id": 101, "name": "John"}'

    result = parser.parse(payload)

    assert len(result) == 1
    assert result[0].record == {
        "customer_id": 101,
        "name": "John"
    }
    assert result[0].success is True


def test_parse_json_array():
    parser = JSONParser()

    payload = [
        {"customer_id": 101, "name": "John"},
        {"customer_id": 102, "name": "Smith"},
    ]

    result = parser.parse(payload)

    assert len(result) == 2
    assert result[0].record == {
        "customer_id": 101,
        "name": "John"
    }
    assert result[1].record == {
        "customer_id": 102,
        "name": "Smith"
    }
    assert result[0].record_number == 1
    assert result[1].record_number == 2
    assert all(item.success for item in result)


def test_parse_json_bytes():
    parser = JSONParser()

    payload = b'{"customer_id": 101, "name": "John"}'

    result = parser.parse(payload)

    assert len(result) == 1
    assert result[0].record == {
        "customer_id": 101,
        "name": "John"
    }
    assert result[0].success is True


def test_invalid_json_raises_parsing_error():
    parser = JSONParser()

    payload = '{"customer_id": 101, "name": John}'

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(payload)

    assert "Invalid JSON payload" in str(exc_info.value)
    assert exc_info.value.format_name == "JSON"


def test_unsupported_payload_type():
    parser = JSONParser()

    payload = 12345

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(payload)

    assert "Unsupported JSON payload type" in str(exc_info.value)


def test_json_parser_rejects_avro_config():
    parser = JSONParser()

    config = ParserConfig(
        format="AVRO",
        schema_source="INLINE",
        schema={
            "type": "record",
            "name": "Customer",
            "fields": [
                {"name": "customer_id", "type": "int"}
            ],
        },
    )

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(b'{"customer_id": 101}', config)

    assert "expected JSON, got AVRO" in str(exc_info.value)


def test_parse_nested_json():
    parser = JSONParser()

    payload = {
        "status": "success",
        "data": {
            "customers": [
                {"customer_id": 101, "name": "John"},
                {"customer_id": 102, "name": "Smith"},
            ]
        },
    }

    config = ParserConfig(
        format="JSON",
        record_path="$.data.customers",
    )

    result = parser.parse(payload, config)

    assert len(result) == 2
    assert result[0].record == {
        "customer_id": 101,
        "name": "John"
    }
    assert result[1].record == {
        "customer_id": 102,
        "name": "Smith"
    }
    assert all(item.success for item in result)


def test_nested_json_path_not_found():
    parser = JSONParser()

    payload = {
        "status": "success",
        "data": {
            "customers": [
                {"customer_id": 101, "name": "John"}
            ]
        }
    }

    config = ParserConfig(
        format="JSON",
        record_path="$.data.orders"
    )

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(payload, config)

    assert "record_path not found" in str(exc_info.value)


def test_invalid_record_path_syntax():
    parser = JSONParser()

    payload = {
        "data": {
            "customers": [
                {"customer_id": 101}
            ]
        }
    }

    config = ParserConfig(
        format="JSON",
        record_path="data.customers"
    )

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(payload, config)

    assert "Unsupported record_path" in str(exc_info.value)


def test_nested_path_returns_invalid_data_type():
    parser = JSONParser()

    payload = {
        "data": {
            "customers": "No customers available"
        }
    }

    config = ParserConfig(
        format="JSON",
        record_path="$.data.customers"
    )

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(payload, config)

    assert "JSON payload must contain an object or array of objects" in str(exc_info.value)


def test_parse_empty_json_array():
    parser = JSONParser()

    result = parser.parse("[]")

    assert result == []


def test_json_array_with_non_object_records():
    parser = JSONParser()

    payload = '[{"customer_id": 101}, "invalid", 123]'

    with pytest.raises(ParsingError) as exc_info:
        parser.parse(payload)

    assert "JSON array must contain only objects" in str(exc_info.value)


def test_parse_json_with_custom_encoding():
    parser = JSONParser()

    payload = '{"customer_id": 101, "name": "José"}'.encode("utf-16")

    config = ParserConfig(
        format="JSON",
        encoding="utf-16"
    )

    result = parser.parse(payload, config)

    assert len(result) == 1
    assert result[0].record == {
        "customer_id": 101,
        "name": "José"
    }
    assert result[0].success is True
