from connectors.demo import DemoConnector
from connectors.registry import ConnectorRegistry


ConnectorRegistry.register(
    "DEMO",
    DemoConnector,
)