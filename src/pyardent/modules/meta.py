import httpx

from ..models import APIStations
from ..models.meta import APIVersion, APIStats, APIEconomies


class MetaModule:

    _client : httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client


    def get_version(self) -> APIVersion:
        response = self._client.get("/version")
        response.raise_for_status()
        return APIVersion.model_validate(response.json())

    def get_stats(self) -> APIStats:
        response = self._client.get("/stats")
        response.raise_for_status()
        return APIStats.model_validate(response.json())

    def get_station_economies(self) -> APIEconomies:
        response = self._client.get("/stats/stations/economies")
        response.raise_for_status()
        return APIEconomies.model_validate(response.json())

    def get_station_types(self) -> APIStations:
        response = self._client.get("/stats/stations/types")
        response.raise_for_status()
        return APIStations.model_validate(response.json())
