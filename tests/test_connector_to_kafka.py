from connectors.registry import ConnectorRegistry
from messaging.producer import FalconKafkaProducer

def test_demo_connector_to_kafka():
    connector_class = ConnectorRegistry.get("DEMO")

    connector = connector_class(
        config={
            "run_id":"integration-run-001"
        }
    )

    producer = FalconKafkaProducer()

    published = []

    try:
        for event in connector.run():
            result = producer.publish(
                topic = "falcon.raw.customer",
                event = event,
                key = str(event.payload["customer_id"]),
            )

            published.append(result)


        producer.flush()

    finally:
        connector.close()
        producer.close()

    assert len(published) == 2

    assert published[0]["topic"] == "falcon.raw.customer"
    assert published[1]["topic"] == "falcon.raw.customer"

    assert published[0]["offset"] >= 0
    assert published[1]["offset"] >= 0