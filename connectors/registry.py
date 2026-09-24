from typing import Type

from connectors.base import BaseConnector


class ConnectorRegistry:
    """
    Registry for Falcon source connectors.

    Maps a connector type such as REST, CSV, POSTGRES, etc.
    to its connector implementation.
    """

    _connectors: dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(
        cls,
        connector_type: str,
        connector_class: Type[BaseConnector],
    ) -> None:
        """
        Register a connector implementation.
        """

        connector_type = connector_type.upper()

        if connector_type in cls._connectors:
            raise ValueError(
                f"Connector already registered: {connector_type}"
            )

        cls._connectors[connector_type] = connector_class

    @classmethod
    def get(cls, connector_type: str) -> Type[BaseConnector]:
        """
        Retrieve a connector class by type.
        """

        connector_type = connector_type.upper()

        connector_class = cls._connectors.get(connector_type)

        if connector_class is None:
            raise ValueError(
                f"Connector not registered: {connector_type}"
            )

        return connector_class

    @classmethod
    def list_connectors(cls) -> list[str]:
        """
        Return all registered connector types.
        """

        return sorted(cls._connectors.keys())