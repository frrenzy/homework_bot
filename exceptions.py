class ImproperlyConfigured(Exception):
    """Exception raised when required configuration is missing."""

    pass


class BaseAPIError(Exception):
    """Exception raised when API returns not OK response."""

    pass


class ResponseTypeError(BaseAPIError, TypeError):
    """Exception raised when response type does not match docs."""

    pass


class EmptyResponseError(ValueError):
    """Exception raised when response.homeworks list is empty."""

    pass


class APIRequestError(BaseAPIError):
    """Exception raised when API returns not OK response."""

    pass
