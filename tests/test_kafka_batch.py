from unittest.mock import MagicMock

import processing.batch

from processing.kafka_batch import KafkaBatchProcessor
from processing.models import KafkaRecord,KafkaBatch

def create_message(customer_id, offset, partition=0):
    message = MagicMock()
    message.value = {"customer_id": customer_id}
    message.topic = "falcon.raw.customer"
    message.partition = partition
    message.offset = offset
    return message


def test_kafka_messages_are_batched():
    consumer = MagicMock()

    messages = [
        create_message(1001, 100),
        create_message(1002, 101),
        create_message(1003, 102),
        create_message(1004, 103),
    ]

    consumer.poll.return_value = {
        "partition-0": messages
    }

    processor = KafkaBatchProcessor(
        consumer=consumer,
        batch_size=2,
        timeout_seconds=30,
    )

    batch = next(processor.process())

    assert batch.records == [
        {"customer_id": 1001},
        {"customer_id": 1002},
    ]
    assert batch.topic == "falcon.raw.customer"
    assert batch.partition == 0
    assert batch.first_offset == 100
    assert batch.last_offset == 101



def test_kafka_batch_flushes_partial_batch():
    consumer = MagicMock()

    processor = KafkaBatchProcessor(
        consumer=consumer,
        batch_size=5,
        timeout_seconds=30,
    )

    builder = processor._get_batch_builder(
        "falcon.raw.customer",
        0,
    )

    builder.add(KafkaRecord(
        value={"customer_id": 1001},
        topic="falcon.raw.customer",
        partition=0,
        offset=100,
    ))
    builder.add(KafkaRecord(
        value={"customer_id": 1002},
        topic="falcon.raw.customer",
        partition=0,
        offset=101,
    ))
    builder.add(KafkaRecord(
        value={"customer_id": 1003},
        topic="falcon.raw.customer",
        partition=0,
        offset=102,
    ))

    partial_batch = processor.flush(
        "falcon.raw.customer",
        0,
    )

    assert partial_batch is not None
    assert partial_batch.records == [
        {"customer_id": 1001},
        {"customer_id": 1002},
        {"customer_id": 1003},
    ]
    assert partial_batch.topic == "falcon.raw.customer"
    assert partial_batch.partition == 0
    assert partial_batch.first_offset == 100
    assert partial_batch.last_offset == 102



def test_flush_empty_batch_returns_none():
    consumer = MagicMock()

    processor = KafkaBatchProcessor(
        consumer=consumer,
        batch_size=2,
        timeout_seconds=30,
    )

    assert processor.flush(
        "falcon.raw.customer",
        0,
    ) is None


def test_kafka_batch_flushes_on_timeout(monkeypatch):
    consumer = MagicMock()

    message = create_message(1001, 100)

    current_time = [100.0]

    monkeypatch.setattr(
        processing.batch,
        "monotonic",
        lambda: current_time[0],
    )

    poll_count = [0]

    def poll_side_effect(timeout_ms):
        poll_count[0] += 1

        if poll_count[0] == 1:
            return {
                "partition-0": [message],
            }

        current_time[0] = 131.0
        return {}

    consumer.poll.side_effect = poll_side_effect

    processor = KafkaBatchProcessor(
        consumer=consumer,
        batch_size=2,
        timeout_seconds=30,
    )

    batch = next(processor.process())

    assert batch.records == [
        {"customer_id": 1001},
    ]
    assert batch.topic == "falcon.raw.customer"
    assert batch.partition == 0
    assert batch.first_offset == 100
    assert batch.last_offset == 100

def test_commit_batch_delegates_to_consumer():
    consumer = MagicMock()

    processor = KafkaBatchProcessor(
        consumer=consumer,
        batch_size=2,
    )

    batch = KafkaBatch(
        records=[
            {"customer_id": 1001},
            {"customer_id": 1002},
        ],
        topic="falcon.raw.customer",
        partition=0,
        first_offset=100,
        last_offset=101,
    )

    processor.commit_batch(batch)

    consumer.commit_batch.assert_called_once_with(
        topic="falcon.raw.customer",
        partition=0,
        last_offset=101,
    )

def test_kafka_partitions_use_separate_batch_builders():
    consumer = MagicMock()
    processor = KafkaBatchProcessor(
        consumer=consumer,
        batch_size=2,
        timeout_seconds=30,
    )

    builder_0 = processor._get_batch_builder(
        "falcon.raw.customer", 0
    )
    builder_1 = processor._get_batch_builder(
        "falcon.raw.customer", 1
    )

    assert builder_0 is not builder_1

    builder_0.add(KafkaRecord(
        value={"customer_id": 1001},
        topic="falcon.raw.customer",
        partition=0,
        offset=100,
    ))
    builder_1.add(KafkaRecord(
        value={"customer_id": 2001},
        topic="falcon.raw.customer",
        partition=1,
        offset=200,
    ))

    batch_0 = processor.flush("falcon.raw.customer", 0)
    batch_1 = processor.flush("falcon.raw.customer", 1)

    assert batch_0 is not None
    assert batch_1 is not None
    assert batch_0.partition == 0
    assert batch_1.partition == 1
    assert batch_0.records == [{"customer_id": 1001}]
    assert batch_1.records == [{"customer_id": 2001}]