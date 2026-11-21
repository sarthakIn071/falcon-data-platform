
import pytest

from parsers.base import BaseParser
from parsers.json_parser import JSONParser
from parsers.avro_parser import AvroParser
from parsers.registry import ParserRegistry


def test_json_parser_is_registered():
    parser_class = ParserRegistry.get("JSON")

    assert parser_class == JSONParser


def test_format_lookup_is_case_insensitive():
    assert ParserRegistry.get("json") == JSONParser
    assert ParserRegistry.get("Json") == JSONParser


def test_list_registered_parsers():
    assert ParserRegistry.list_parsers() == ["AVRO","JSON"]


def test_unknown_parser_raises_error():
    with pytest.raises(ValueError, match="Parser not registered"):
        ParserRegistry.get("XML")


def test_registry_returns_parser_class():
    parser_class = ParserRegistry.get("JSON")

    assert issubclass(parser_class, BaseParser)


def test_registered_parser_can_be_instantiated():
    parser_class = ParserRegistry.get("JSON")
    parser = parser_class()

    assert isinstance(parser, JSONParser)

# ------------------------- AVRO PARSERS --------------------------


def test_avro_parser_is_registered():
    assert ParserRegistry.get("AVRO") == AvroParser


def test_avro_lookup_is_case_insensitive():
    assert ParserRegistry.get("avro") == AvroParser
    assert ParserRegistry.get("Avro") == AvroParser


def test_registered_avro_parser_can_be_instantiated():
    parser_class = ParserRegistry.get("AVRO")
    parser = parser_class()

    assert isinstance(parser, AvroParser)