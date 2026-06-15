import logging

import httpx

from ..models import Station

logger = logging.getLogger("pyardent.models.station")

class StationModule:
    _client: httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client

    def get_by_id(self, id: str | int) -> Station:
        logger.debug(f"GET /market/{id}")
        response = self._client.get(f"/market/{id}")
        station_data = response.json()
        return Station.from_json(self._client, station_data)