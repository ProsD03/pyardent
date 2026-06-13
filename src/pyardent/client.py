import logging

import httpx
from .modules import MetaModule
from .exceptions import PyArdentError, ResourceNotFoundError

logger = logging.getLogger("pyardent.client")


def _handle_response_errors(response: httpx.Response):
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:

        logger.error(f"HTTP error {e.response.status_code} for URL: {response.url}")

        if e.response.status_code == 404:
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

    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or self.DEFAULT_BASE_URL

        self._client = httpx.Client(base_url=self._base_url, event_hooks={"response": [_handle_response_errors, ]})
        self.meta = MetaModule(self._client)

        logger.info(f"Initialized ArdentClient pointing to {self._base_url}")
