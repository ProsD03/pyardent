import logging

import httpx
from .modules import MetaModule, CommodityModule, SystemModule
from .exceptions import PyArdentError, ResourceNotFoundError, CommodityNotFoundError, SystemNotFoundError
from .modules.station import StationModule

logger = logging.getLogger("pyardent.client")


def _handle_response_errors(response: httpx.Response):
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
                else:
                    raise PyArdentError(api_msg) from e
            raise ResourceNotFoundError(str(response.url)) from e
        else:
            raise PyArdentError(f"HTTP error {e.response.status_code} for URL: {response.url}") from e
    except httpx.RequestError as e:
        logger.error(f"Network error while connecting to {e.request.url}: {e}")
        raise PyArdentError(f"Network error: {str(e)}") from e


class ArdentClient:
    DEFAULT_BASE_URL = "https://api.ardent-insight.com/v2"
    _client: httpx.Client

    meta: MetaModule
    commodity: CommodityModule
    system: SystemModule
    station: StationModule

    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or self.DEFAULT_BASE_URL

        self._client = httpx.Client(base_url=self._base_url, event_hooks={"response": [_handle_response_errors, ]})

        self.meta = MetaModule(self._client)
        self.commodity = CommodityModule(self._client)
        self.system = SystemModule(self._client)
        self.station = StationModule(self._client)

        logger.info(f"Initialized ArdentClient pointing to {self._base_url}")
