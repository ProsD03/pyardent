import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from .system import System

logger = logging.getLogger("pyardent.models.station")

class StationData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system_address: int
    system_name: str
    station_id: int = Field(alias="marketId")
    station_name: str
    station_type: str | None = None
    primary_economy: str | None = None
    secondary_economy: str | None = None
    distance_to_arrival: float | None = None
    max_landing_pad_size: int | None = None
    allegiance: str | None = None
    government: str | None = None
    controlling_faction: str | None = None
    updated_at: datetime | None = None

class Station(StationData):
    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "Station":
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_system(self)-> "System":
        from .system import System

        logger.debug(f"GET /system/address/{self.system_address}")
        response = self._client.get(f"/system/address/{self.system_address}")
        system = response.json()
        return System.from_json(self._client, system)