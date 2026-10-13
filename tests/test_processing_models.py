from processing.models import KafkaBatch, KafkaRecord

def test_kafka_record():
    record = KafkaRecord(
        value={"customer_id": 1001},
        topic="falcon.raw.customer",
        partition=0,
        offset=100,
    )

    assert record.value == {"customer_id": 1001}
    assert record.topic == "falcon.raw.customer"
    assert record.partition == 0
    assert record.offset == 100

def test_kafka_batch():
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

    assert len(batch.records) == 2
    assert batch.topic == "falcon.raw.customer"
    assert batch.partition == 0
    assert batch.first_offset == 100
    assert batch.last_offset == 101