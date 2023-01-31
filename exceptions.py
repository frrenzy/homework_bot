class BaseError(Exception):
    """Base exception."""

    pass


class ImproperlyConfigured(BaseError):
    """Exception raised when required configuration is missing."""

    pass


class BaseAPIError(BaseError):
    """Exception raised when API returns not OK response."""

    pass


class ResponseTypeError(BaseAPIError, TypeError):
    """Exception raised when response type does not match docs."""

    pass


class EmptyResponseError(BaseError):
    """Exception raised when response.homeworks list is empty."""

    pass


class APIRequestError(BaseAPIError):
    """Exception raised when API returns not OK response."""

    pass
