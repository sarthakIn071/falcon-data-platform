class ConnectorError(Exception):
    """
    Base exception for all Falcon connector errors.
    """

    pass


class ConnectorConnectionError(ConnectorError):
    """
    Raised when a connector cannot connect to its source.
    """

    pass


class ConnectorExtractionError(ConnectorError):
    """
    Raised when a connector fails while extracting records.
    """

    pass


class ConnectorEventError(ConnectorError):
    """
    Raised when a source record cannot be converted
    into a FalconEvent.
    """

    pass