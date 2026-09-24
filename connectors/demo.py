from typing import Iterator

from connectors.base import BaseConnector
from messaging.event import FalconEvent, SourceInfo


class DemoConnector(BaseConnector):
    """
    Simple connector used to test the Falcon connector framework.
    """

    def connect(self) -> None:
        print("DemoConnector connected")

    def extract(self) -> Iterator[dict]:
        records = [
            {
                "customer_id": 1001,
                "name": "John",
                "email": "john@example.com",
            },
            {
                "customer_id": 1002,
                "name": "Sarah",
                "email": "sarah@example.com",
            },
        ]

        yield from records

    def to_event(self, record: dict) -> FalconEvent:
        return FalconEvent(
            event_id=f"customer-{record['customer_id']}",
            run_id=self.config.get("run_id", "demo-run"),
            source=SourceInfo(
                type="DEMO",
                connector="demo_connector",
                system="falcon-demo",
            ),
            entity="customer",
            operation="UPSERT",
            payload=record,
        )

    def close(self) -> None:
        print("DemoConnector closed")