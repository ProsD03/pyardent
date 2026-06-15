import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, PrivateAttr, ConfigDict
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from .station import Station

logger = logging.getLogger("pyardent.models.system")

class SystemData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system_address: int
    system_name: str
    system_x: float
    system_y: float
    system_z: float
    system_sector: str
    updated_at: datetime

class System(SystemData):
    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "System":
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_stations(self) -> list["Station"]:
        from .station import Station

        logger.debug(f"GET /system/address/{self.system_address}/markets")
        response = self._client.get(f"/system/address/{self.system_address}/markets")
        stations = response.json()
        logger.debug(f"Parsing {len(stations)} stations")
        return [Station.from_json(self._client, station) for station in stations]
