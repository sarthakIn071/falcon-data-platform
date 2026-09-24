from connectors.registry import ConnectorRegistry
from connectors.demo import DemoConnector
from messaging.event import FalconEvent


def test_demo_connector_registered():
    connector_class = ConnectorRegistry.get("DEMO")

    assert connector_class is DemoConnector


def test_demo_connector_produces_events():
    connector = DemoConnector(
        config={
            "run_id": "test-run-001"
        }
    )

    events = list(connector.run())

    assert len(events) == 2

    assert isinstance(events[0], FalconEvent)
    assert isinstance(events[1], FalconEvent)

    assert events[0].entity == "customer"
    assert events[0].operation == "UPSERT"

    assert events[0].payload["customer_id"] == 1001
    assert events[1].payload["customer_id"] == 1002

    assert events[0].run_id == "test-run-001"
    assert events[1].run_id == "test-run-001"