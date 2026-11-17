
from unittest.mock import Mock

import pytest

from messaging.event import FalconEvent, SourceInfo
from messaging.producer import (
    FalconKafkaProducer,
    FalconKeySerializer,
    FalconValueSerializer,
)


@pytest.fixture
def sample_event():
    return FalconEvent(
        event_id="event-001",
        run_id="run-001",
        source=SourceInfo(
            type="REST_API",
            connector="demo_connector",
            system="demo",
        ),
        entity="customer",
        operation="UPSERT",
        payload={
            "customer_id": 1001,
            "name": "John",
            "email": "john@example.com",
        },
    )


@pytest.fixture
def mock_kafka(monkeypatch):
    mock_producer = Mock()

    metadata = Mock()
    metadata.topic = "falcon.raw.customer"
    metadata.partition = 0
    metadata.offset = 81

    future = Mock()
    future.get.return_value = metadata

    mock_producer.send.return_value = future

    monkeypatch.setattr(
        "messaging.producer.KafkaProducer",
        Mock(return_value=mock_producer),
    )

    return mock_producer


def test_value_serializer():
    serializer = FalconValueSerializer()

    result = serializer.serialize(
        "falcon.raw.customer",
        [],
        {"customer_id": 1001, "name": "John"},
    )

    assert result == b'{"customer_id": 1001, "name": "John"}'


def test_value_serializer_none():
    serializer = FalconValueSerializer()

    assert serializer.serialize("test", [], None) is None


def test_key_serializer():
    serializer = FalconKeySerializer()

    result = serializer.serialize(
        "falcon.raw.customer",
        [],
        "1001",
    )

    assert result == b"1001"


def test_key_serializer_none():
    serializer = FalconKeySerializer()

    assert serializer.serialize("test", [], None) is None


def test_publish_event(mock_kafka, sample_event):
    producer = FalconKafkaProducer()

    result = producer.publish(
        topic="falcon.raw.customer",
        event=sample_event,
        key="1001",
    )

    assert result == {
        "topic": "falcon.raw.customer",
        "partition": 0,
        "offset": 81,
    }

    mock_kafka.send.assert_called_once_with(
        "falcon.raw.customer",
        key="1001",
        value=sample_event.model_dump(mode="json"),
    )


def test_publish_failure(mock_kafka, sample_event):
    mock_kafka.send.return_value.get.side_effect = TimeoutError(
        "Kafka publish timeout"
    )

    producer = FalconKafkaProducer()

    with pytest.raises(TimeoutError):
        producer.publish(
            topic="falcon.raw.customer",
            event=sample_event,
            key="1001",
        )


def test_flush(mock_kafka):
    producer = FalconKafkaProducer()

    producer.flush()

    mock_kafka.flush.assert_called_once()


def test_close(mock_kafka):
    producer = FalconKafkaProducer()

    producer.close()

    mock_kafka.close.assert_called_once()
