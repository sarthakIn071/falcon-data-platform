from connectors.registry import ConnectorRegistry
from messaging.event import FalconEvent, SourceInfo

def test_rest_connector():
    connector_class = ConnectorRegistry.get("REST")

    connector = connector_class(
        config = {
            "url": "https://jsonplaceholder.typicode.com/users",
            "run_id": "rest-test-001",
            "entity": "customer",
            "system": "jsonplaceholder",
            "headers": {
            "Accept": "application/json",
        },

        }
    )

    events = list(connector.run())

    assert len(events) > 0

    assert isinstance(events[0], FalconEvent)

    assert events[0].entity == "customer"
    assert events[0].operation == "UPSERT"

    assert "id" in events[0].payload
    assert "name" in events[0].payload
    assert "email" in events[0].payload

    assert events[0].run_id == "rest-test-001"