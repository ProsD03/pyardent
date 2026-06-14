
class PyArdentError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class ResourceNotFoundError(PyArdentError):
    def __init__(self, url: str):
        super().__init__(f"Resource not found at endpoint: {url}")

class CommodityNotFoundError(PyArdentError):
    def __init__(self, url: str):
        super().__init__(f"Commodity does not exist. Endpoint: {url}")