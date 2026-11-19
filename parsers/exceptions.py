class ParsingError(Exception):
    """
    Raised when a source payload cannot be parsed.
    """

    def __init__(self, message: str, format_name: str | None = None):
        self.format_name = format_name
        super().__init__(message)