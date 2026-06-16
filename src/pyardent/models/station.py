import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr, model_validator
from pydantic.alias_generators import to_camel

from ..types import LandingPad

if TYPE_CHECKING:
    from .system import System
    from .commodity import Commodity
    from .market import CommodityMarket

logger = logging.getLogger("pyardent.models.station")

class StationServiceFlags(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    shipyard: bool | None = None
    outfitting: bool | None = None
    black_market: bool | None = None
    contacts: bool | None = None
    crew_lounge: bool | None = None
    interstellar_factors: bool | None = None
    material_trader: bool | None = None
    missions: bool | None = None
    refuel: bool | None = None
    repair: bool | None = None
    restock: bool | None = None
    search_and_rescue: bool | None = None
    technology_broker: bool | None = None
    tuning: bool | None = None
    universal_cartographics: bool | None = None

class StationLocation(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    distance_to_arrival: float | None = None
    body_id: int | None = None
    body_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class StationData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system_address: int
    station_id: int = Field(alias="marketId")
    station_name: str
    station_type: str | None = None
    primary_economy: str | None = None
    secondary_economy: str | None = None

    services: StationServiceFlags | None = None
    location: StationLocation | None = None

    max_landing_pad_size: LandingPad | None = None
    allegiance: str | None = None
    government: str | None = None
    controlling_faction: str | None = None
    updated_at: datetime | None = None

    @model_validator(mode='before')
    @classmethod
    def explode_flat_data(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        service_keys = [
            "shipyard", "outfitting", "blackMarket", "contacts", "crewLounge",
            "interstellarFactors", "materialTrader", "missions", "refuel",
            "repair", "restock", "searchAndRescue", "technologyBroker",
            "tuning", "universalCartographics"
        ]

        services = {k: data.pop(k, None) for k in service_keys}
        data["services"] = services

        location_keys = [
            "distanceToArrival", "bodyId", "bodyName", "latitude", "longitude"
        ]

        location = {k: data.pop(k, None) for k in location_keys}
        data["location"] = location

        return data

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

    def get_full_details(self) -> "Station":
        if self.location and self.location.body_id is not None:
            return self

        logger.debug(f"GET /market/{self.station_id}")
        response = self._client.get(f"/market/{self.station_id}")
        station_data = response.json()
        station = Station.from_json(self._client, station_data)
        self.__dict__.update(station.__dict__)
        return self

    def get_commodity_market(self, commodity: "Commodity") -> "CommodityMarket":
        from .market import CommodityMarket

        logger.debug(f"GET /market/{self.station_id}/commodity/name/{commodity.commodity_name}")
        response = self._client.get(f"/market/{self.station_id}/commodity/name/{commodity.commodity_name}")
        commodity_data = response.json()
        return CommodityMarket.from_json(self._client, commodity_data)
