from connectors.registry import ConnectorRegistry
from messaging.producer import FalconKafkaProducer


def test_rest_connector_to_kafka():
    connector_class = ConnectorRegistry.get("REST")

    connector = connector_class(
        config={
            "url": "https://jsonplaceholder.typicode.com/users",
            "run_id": "rest-kafka-run-001",
            "entity": "customer",
            "system": "jsonplaceholder",
        }
    )

    producer = FalconKafkaProducer()

    published=[]

    try:
        for event in connector.run():
            result = producer.publish(
                topic="falcon.raw.customer",
                event=event,
                key=str(event.payload["id"]),
            )

            published.append(result)

        producer.flush()

    finally:
        connector.close()
        producer.close()

    assert len(published) == 10

    for result in published:
        assert result["topic"] == "falcon.raw.customer"
        assert result["offset"] >= 0