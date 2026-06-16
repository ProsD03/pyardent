"""Exception hierarchy raised by pyardent.

All errors raised by the client are `PyArdentError` or one of its subclasses
below, translated from HTTP responses by `client._handle_response_errors`.
"""


class PyArdentError(Exception):
    """Base class for all errors raised by this library.

    Args:
        message: Human-readable description of the failure.
    """

    def __init__(self, message: str):
        super().__init__(message)

class ResourceNotFoundError(PyArdentError):
    """Raised on a 404 whose API error message didn't match a more specific case.

    Args:
        url: The request URL that returned the 404.
    """

    def __init__(self, url: str):
        super().__init__(f"Resource not found at endpoint: {url}")

class CommodityNotFoundError(PyArdentError):
    """Raised when the requested commodity does not exist.

    Args:
        url: The request URL that returned the 404.
    """

    def __init__(self, url: str):
        super().__init__(f"Commodity does not exist. Endpoint: {url}")

class SystemNotFoundError(PyArdentError):
    """Raised when the requested system does not exist.

    Args:
        url: The request URL that returned the 404.
    """

    def __init__(self, url: str):
        super().__init__(f"System does not exist. Endpoint: {url}")

class ServiceNotFoundError(PyArdentError):
    """Raised when the requested station service type is unknown to the API.

    Args:
        url: The request URL that returned the 404.
    """

    def __init__(self, url: str):
        super().__init__(f"Service does not exist. Endpoint: {url}")