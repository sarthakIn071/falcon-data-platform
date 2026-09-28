class ValidationError(Exception):
    """
    Base exception for validation-related errors.
    """

    pass


class SchemaValidationError(ValidationError):
    """
    Raised when a record fails schema validation.
    """

    pass


class QuarantineError(ValidationError):
    """
    Raised when an item cannot be moved to quarantine.
    """

    pass