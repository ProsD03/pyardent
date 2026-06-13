import logging

import httpx

from ..models import APIStations
from ..models.meta import APIVersion, APIStats, APIEconomies

logger = logging.getLogger("pyardent.modules.meta")

class MetaModule:

    _client : httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client


    def get_version(self) -> APIVersion:
        logger.debug("GET /version")
        response = self._client.get("/version")
        return APIVersion.model_validate(response.json())

    def get_stats(self) -> APIStats:
        logger.debug("GET /stats")
        response = self._client.get("/stats")
        return APIStats.model_validate(response.json())

    def get_station_economies(self) -> APIEconomies:
        logger.debug("GET /stats/stations/economies")
        response = self._client.get("/stats/stations/economies")
        return APIEconomies.model_validate(response.json())

    def get_station_types(self) -> APIStations:
        logger.debug("GET /stats/stations/types")
        response = self._client.get("/stats/stations/types")
        return APIStations.model_validate(response.json())
