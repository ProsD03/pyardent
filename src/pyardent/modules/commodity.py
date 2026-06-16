import logging
from urllib.parse import unquote, quote

import httpx

from ..models.commodity import Commodity

logger = logging.getLogger("pyardent.modules.commodity")

class CommodityModule:
    _ALIASES = {
        "voidopal": "opal"
    }
    _client: httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client

    def get_all(self) -> list[Commodity]:
        logger.debug("GET /commodities")
        response = self._client.get("/commodities")
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        parsed_commodities = [Commodity.from_json(self._client, commodity) for commodity in commodities]
        return parsed_commodities

    def get_by_name(self, name: str) -> Commodity:
        normalized_name = unquote(name).lower().strip().replace(" ", "")
        if not normalized_name:
            raise ValueError("name cannot be empty")

        if normalized_name in self._ALIASES:
            logger.debug(f"Alias found: {normalized_name} -> {self._ALIASES[normalized_name]}")

        url_encoded_name = self._ALIASES.get(normalized_name, normalized_name)
        url_encoded_name = quote(url_encoded_name, safe = '')

        logger.debug(f"GET /commodity/name/{url_encoded_name}")
        response = self._client.get(f"/commodity/name/{url_encoded_name}")
        commodity_data = response.json()
        return Commodity.from_json(self._client, commodity_data)