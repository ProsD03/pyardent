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
        if not normalized_name:
            raise ValueError("name cannot be empty")
        url_encoded_name = quote(normalized_name, safe='')

        logger.debug(f"GET /system/name/{url_encoded_name}")
        response = self._client.get(f"/system/name/{url_encoded_name}")
        return System.from_json(self._client, payload=response.json())

    def get_by_address(self, address: str | int) -> System:
        normalized_address = str(address).strip()
        if not normalized_address:
            raise ValueError("address cannot be empty")
        if isinstance(address, int) and address < 0:
            raise ValueError(f"address cannot be negative. received: {address}")
        url_encoded_address = quote(normalized_address, safe='')

        logger.debug(f"GET /system/address/{url_encoded_address}")
        response = self._client.get(f"/system/address/{url_encoded_address}")
        return System.from_json(self._client, payload=response.json())
