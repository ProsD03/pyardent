import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, PrivateAttr, ConfigDict
from pydantic.alias_generators import to_camel

from ..types import StationServices, LandingPad

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

    def get_nearby_systems(self, max_distance: int = 100, hide_debug_system: bool = True) -> list["System"]:
        if max_distance > 500 or max_distance < 0:
            raise ValueError(f"max_distance must be between 0 and 500. received: {max_distance}")

        logger.debug(f"GET /system/address/{self.system_address}/nearby")
        response = self._client.get(f"/system/address/{self.system_address}/nearby", params={"maxDistance": max_distance})
        systems = response.json()
        logger.debug(f"Parsing {len(systems)} nearby systems")
        return [
            System.from_json(self._client, system)
            for system in systems
            if not hide_debug_system or system.get("systemName") != "TestRender"
        ]

    def get_nearest_service(self, service: StationServices, min_landing_pad_size: LandingPad | None = None) -> list["Station"]:
        from .station import Station

        if min_landing_pad_size:
            params = {
            "minLandingPadSize": min_landing_pad_size.value,
            }
        else:
            params = {}

        logger.debug(f"GET /system/address/{self.system_address}/nearest/{service.value}")
        response = self._client.get(f"/system/address/{self.system_address}/nearest/{service.value}", params=params)
        stations = response.json()
        return [Station.from_json(self._client, station) for station in stations]