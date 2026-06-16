"""Top-level client for the Ardent Insight API.

Wires up an `httpx.Client` shared by all `*Module` instances and installs the
response hook that translates HTTP error responses into `PyArdentError`
subclasses.
"""

import logging

import httpx
from .modules import MetaModule, CommodityModule, SystemModule
from .exceptions import PyArdentError, ResourceNotFoundError, CommodityNotFoundError, SystemNotFoundError, \
    ServiceNotFoundError
from .modules.station import StationModule

logger = logging.getLogger("pyardent.client")


def _handle_response_errors(response: httpx.Response):
    """Translate failed HTTP responses into `PyArdentError` subclasses.

    Registered as an `httpx.Client` "response" event hook, so it runs on
    every request made through `ArdentClient`. Successful responses pass
    through unchanged.

    Args:
        response: The `httpx.Response` returned by the underlying request.

    Raises:
        CommodityNotFoundError: On a 404 whose API error message mentions a commodity.
        SystemNotFoundError: On a 404 whose API error message mentions a system.
        ServiceNotFoundError: On a 404 whose API error message mentions a service.
        ResourceNotFoundError: On a 404 with no recognizable error message.
        PyArdentError: On any other HTTP error status, a 404 with an
            unrecognized message, or a network-level error.
    """
    response.read()
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:

        logger.error(f"HTTP error {e.response.status_code} for URL: {response.url}")

        if e.response.status_code == 404:
            error_payload = e.response.json()
            api_msg = error_payload.get("message")
            if api_msg:
                if "commodity" in api_msg.lower():
                    raise CommodityNotFoundError(str(response.url)) from e
                elif "system" in api_msg.lower():
                    raise SystemNotFoundError(str(response.url)) from e
                elif "service" in api_msg.lower():
                    raise ServiceNotFoundError(str(response.url)) from e
                else:
                    raise PyArdentError(api_msg) from e
            raise ResourceNotFoundError(str(response.url)) from e
        else:
            raise PyArdentError(f"HTTP error {e.response.status_code} for URL: {response.url}") from e
    except httpx.RequestError as e:
        logger.error(f"Network error while connecting to {e.request.url}: {e}")
        raise PyArdentError(f"Network error: {str(e)}") from e


class ArdentClient:
    """Entry point for the Ardent Insight API client.

    Holds the shared `httpx.Client` and exposes one module per API resource
    area (`meta`, `commodity`, `system`, `station`). Methods on those modules
    return rich pydantic models (e.g. `System`, `Station`, `Commodity`,
    `CommodityMarket`) that carry a reference back to this client so they can
    make further API calls themselves (e.g. `system.get_stations()`).
    """

    DEFAULT_BASE_URL = "https://api.ardent-insight.com/v2"
    _client: httpx.Client

    meta: MetaModule
    commodity: CommodityModule
    system: SystemModule
    station: StationModule

    def __init__(self, base_url: str | None = None):
        """Create a client and its underlying HTTP session.

        Args:
            base_url: Override for the API base URL. Defaults to
                `ArdentClient.DEFAULT_BASE_URL` when omitted.
        """
        self._base_url = base_url or self.DEFAULT_BASE_URL

        self._client = httpx.Client(base_url=self._base_url, event_hooks={"response": [_handle_response_errors, ]})

        self.meta = MetaModule(self._client)
        self.commodity = CommodityModule(self._client)
        self.system = SystemModule(self._client)
        self.station = StationModule(self._client)

        logger.info(f"Initialized ArdentClient pointing to {self._base_url}")
