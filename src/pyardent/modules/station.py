import logging
from urllib.parse import quote, unquote

import httpx

from ..models import Station

logger = logging.getLogger("pyardent.modules.station")

class StationModule:
    _client: httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client

    def get_by_id(self, id: str | int) -> Station:
        normalized_id = str(id).strip()
        if not normalized_id:
            raise ValueError("id cannot be empty")
        if isinstance(id, int) and id < 0:
            raise ValueError(f"id cannot be negative. received: {id}")
        url_encoded_id = quote(normalized_id, safe='')

        logger.debug(f"GET /market/{url_encoded_id}")
        response = self._client.get(f"/market/{url_encoded_id}")
        station_data = response.json()
        return Station.from_json(self._client, station_data)

    def search_by_name(self, name: str) -> list[Station]:
        normalized_name = unquote(name).lower().strip()
        if not normalized_name:
            raise ValueError("name cannot be empty")
        url_encoded_name = quote(normalized_name, safe='')

        logger.debug(f"GET /search/station/name/{url_encoded_name}")
        response = self._client.get(f"/search/station/name/{url_encoded_name}")
        stations = response.json()
        logger.debug(f"Parsing {len(stations)} matching stations")
        return [Station.from_json(self._client, station) for station in stations]