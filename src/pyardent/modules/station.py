"""Entry point for the API's station/market resource (`/market/...`, `/search/station/...`)."""

import logging
from urllib.parse import quote, unquote

import httpx

from ..models import Station

logger = logging.getLogger("pyardent.modules.station")

class StationModule:
    """Attached as `ArdentClient.station`. Looks up stations to start traversing from."""

    _client: httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client

    def get_by_id(self, id: str | int) -> Station:
        """Fetch one station by its market ID.

        Args:
            id: The station's market ID.

        Returns:
            The matching `Station`.

        Raises:
            ValueError: If `id` is empty, or negative when given as an int.
            ResourceNotFoundError: If no station matches.
        """
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
        """Search for stations whose name starts with the given text.

        This is a prefix search (suitable for autocomplete), not an exact
        match, and may return stations of the same name in different systems.

        Args:
            name: The name prefix to search for. Case-insensitive.

        Returns:
            Up to 25 matching stations.

        Raises:
            ValueError: If `name` is empty after normalization.
        """
        normalized_name = unquote(name).lower().strip()
        if not normalized_name:
            raise ValueError("name cannot be empty")
        url_encoded_name = quote(normalized_name, safe='')

        logger.debug(f"GET /search/station/name/{url_encoded_name}")
        response = self._client.get(f"/search/station/name/{url_encoded_name}")
        stations = response.json()
        logger.debug(f"Parsing {len(stations)} matching stations")
        return [Station.from_json(self._client, station) for station in stations]