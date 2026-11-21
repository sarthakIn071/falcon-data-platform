
from connectors.registry import ConnectorRegistry
from messaging.producer import FalconKafkaProducer
import connectors.rest as rest_module
import httpx


def test_rest_connector_to_kafka(monkeypatch):
    api_records = [
        {"id": 1, "name": "John", "email": "john@example.com"},
        {"id": 2, "name": "Alice", "email": "alice@example.com"},
    ]

    def mock_get(url, headers=None, params=None, timeout=None):
        return httpx.Response(
            200,
            json=api_records,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(rest_module.httpx, "get", mock_get)

    connector_class = ConnectorRegistry.get("REST")

    connector = connector_class(
        config={
            "url": "https://example.test/users",
            "run_id": "rest-kafka-run-001",
            "entity": "customer",
            "system": "test-api",
        }
    )

    producer = FalconKafkaProducer()
    published = []

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

    assert len(published) == 2

    for result in published:
        assert result["topic"] == "falcon.raw.customer"
        assert result["offset"] >= 0
