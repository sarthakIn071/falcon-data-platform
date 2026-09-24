from connectors.demo import DemoConnector
from connectors.rest import RestConnector
from connectors.registry import ConnectorRegistry


ConnectorRegistry.register(
    "DEMO",
    DemoConnector,
)

ConnectorRegistry.register(
    "REST",
    RestConnector,
)