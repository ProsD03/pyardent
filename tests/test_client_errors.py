import httpx
import pytest
import respx
from httpx import Response

from pyardent import ArdentClient, SystemNotFoundError, CommodityNotFoundError, ServiceNotFoundError, PyArdentError, ResourceNotFoundError

@respx.mock
def test_system_not_found():
    respx.get("https://api.ardent-insight.com/v2/system/name/nonexistent").mock(return_value=Response(404, json={"error": "Not Found", "message": "System not found"}))

    client = ArdentClient()

    with pytest.raises(SystemNotFoundError):
        client.system.get_by_name("nonexistent")

@respx.mock
def test_commodity_not_found():
    respx.get("https://api.ardent-insight.com/v2/commodity/name/nonexistent").mock(return_value=Response(404, json={"error": "Not Found", "message": "Commodity not found"}))

    client = ArdentClient()

    with pytest.raises(CommodityNotFoundError):
        client.commodity.get_by_name("nonexistent")

@respx.mock
def test_service_not_found():
    respx.get("https://api.ardent-insight.com/v2/system/name/nonexistent").mock(
        return_value=Response(404, json={"error": "Not Found", "message": "Service not found"})
    )

    client = ArdentClient()

    with pytest.raises(ServiceNotFoundError):
        client.system.get_by_name("nonexistent")

@respx.mock
def test_resource_not_found():
    respx.get("https://api.ardent-insight.com/v2/system/name/nonexistent").mock(return_value=Response(404, json={"error": "Not Found"}))

    client = ArdentClient()
    with pytest.raises(ResourceNotFoundError):
        client.system.get_by_name("nonexistent")

@respx.mock
def test_pyardent_error_500():
    respx.get("https://api.ardent-insight.com/v2/system/name/nonexistent").mock(return_value=Response(500, json={"error": "Internal Server Error"}))

    client = ArdentClient()
    with pytest.raises(PyArdentError):
        client.system.get_by_name("nonexistent")

@respx.mock
def test_pyardent_error_unknown404():
    respx.get("https://api.ardent-insight.com/v2/system/name/nonexistent").mock(return_value=Response(404, json={"error": "Not Found", "message": "Unknown error"}))

    client = ArdentClient()
    with pytest.raises(PyArdentError):
        client.system.get_by_name("nonexistent")

@respx.mock
def test_pyardent_error_connection_error():
    respx.get("https://api.ardent-insight.com/v2/system/name/nonexistent").mock(side_effect=httpx.ConnectError("Address is unreachable"))

    client = ArdentClient()
    with pytest.raises(httpx.ConnectError):
        client.system.get_by_name("nonexistent")