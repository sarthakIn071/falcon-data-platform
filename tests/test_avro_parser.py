
from io import BytesIO

from fastavro import writer

import pytest

from parsers.avro_parser import AvroParser
from parsers.exceptions import ParsingError
from parsers.models import ParserConfig


AVRO_SCHEMA = {
    "type": "record",
    "name": "Customer",
    "fields": [
        {"name": "customer_id", "type": "int"},
        {"name": "name", "type": "string"},
    ],
}


def make_config():
    return ParserConfig(
        format="AVRO",
        schema_source="INLINE",
        schema=AVRO_SCHEMA,
    )


def make_avro_data():
    stream = BytesIO()

    records = [
        {"customer_id": 1001, "name": "John"},
        {"customer_id": 1002, "name": "Alice"},
        {"customer_id": 1003, "name": "David"},
    ]

    writer(stream, AVRO_SCHEMA, records)

    return stream.getvalue(), records


def test_parse_avro_bytes():
    parser = AvroParser()
    payload, expected_records = make_avro_data()

    records = parser.parse(payload, make_config())

    assert len(records) == len(expected_records)

    for index, result in enumerate(records):
        assert result.success is True
        assert result.record == expected_records[index]
        assert result.record_number == index + 1


def test_parse_avro_stream():
    parser = AvroParser()
    payload, expected_records = make_avro_data()

    stream = BytesIO(payload)

    results = list(
        parser.parse_stream(stream, make_config())
    )

    assert len(results) == len(expected_records)

    for index, result in enumerate(results):
        assert result.success is True
        assert result.record == expected_records[index]
        assert result.record_number == index + 1

def test_parse_invalid_avro_data():
    parser = AvroParser()

    with pytest.raises(ParsingError):
        parser.parse(
            b"this is not an avro file",
            make_config(),
        )


def test_avro_parser_requires_configuration():
    parser = AvroParser()

    with pytest.raises(ParsingError):
        parser.parse(b"invalid avro data")
