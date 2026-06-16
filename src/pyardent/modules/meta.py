"""Entry point for the API's metadata/statistics endpoints."""

import logging

import httpx

from ..models import APIStations
from ..models.meta import APIVersion, APIStats, APIEconomies

logger = logging.getLogger("pyardent.modules.meta")

class MetaModule:
    """Attached as `ArdentClient.meta`. Wraps `/version` and `/stats*`.

    Unlike `CommodityModule`/`SystemModule`/`StationModule`, the models
    returned here are flat DTOs validated directly with `model_validate`
    rather than `from_json`, since they don't need a `_client` reference —
    there's nothing further to traverse to from a stats snapshot.
    """

    _client : httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client


    def get_version(self) -> APIVersion:
        """Fetch the running Ardent API software version.

        Returns:
            The API version.
        """
        logger.debug("GET /version")
        response = self._client.get("/version")
        return APIVersion.model_validate(response.json())

    def get_stats(self) -> APIStats:
        """Fetch database-wide counters (systems, stations, trade orders, etc).

        Returns:
            Stats refreshed every 15 minutes by the API.
        """
        logger.debug("GET /stats")
        response = self._client.get("/stats")
        return APIStats.model_validate(response.json())

    def get_station_economies(self) -> APIEconomies:
        """Fetch station counts grouped by primary/secondary economy.

        Returns:
            Economy breakdown, excluding fleet carriers (reported separately).
        """
        logger.debug("GET /stats/stations/economies")
        response = self._client.get("/stats/stations/economies")
        return APIEconomies.model_validate(response.json())

    def get_station_types(self) -> APIStations:
        """Fetch station counts grouped by station type.

        Returns:
            Station type breakdown.
        """
        logger.debug("GET /stats/stations/types")
        response = self._client.get("/stats/stations/types")
        return APIStations.model_validate(response.json())
