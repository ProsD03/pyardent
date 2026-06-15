import logging
from urllib.parse import unquote, quote

import httpx

from ..models import System

logger = logging.getLogger("pyardent.modules.system")

class SystemModule:
    _client: httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client

    def get_by_name(self, name: str) -> System:
        normalized_name = unquote(name).lower().strip().replace(" ", "")
        url_encoded_name = quote(normalized_name, safe='')

        logger.debug(f"GET /system/name/{url_encoded_name}")
        response = self._client.get(f"/system/name/{url_encoded_name}")
        return response.json()

    def get_by_address(self, address: str | int) -> System:
        logger.debug(f"GET /system/address/{address}")
        response = self._client.get(f"/system/address/{address}")
        return response.json()