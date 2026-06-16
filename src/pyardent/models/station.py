"""Models for the API's station/market resource (`/market/{marketId}/...`).

`Station` is a graph-traversal node, not a flat DTO: its `get_*` methods make
further API calls rooted at `self.station_id` and return other rich models
(`System`, `CommodityMarket`).

`StationServiceFlags` and `StationLocation` are internal building blocks of
`Station` and aren't meant to be constructed directly — they're only ever
populated via `Station.from_json`.
"""

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
    """Which services a station offers, as a flat set of booleans.

    All fields are `None` rather than `False` when the API didn't report a
    value for that service at all (as opposed to reporting it absent).
    """

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
    """Where a station sits relative to its system's main star and body."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    distance_to_arrival: float | None = None
    body_id: int | None = None
    body_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class StationData(BaseModel):
    """Plain fields of a station, as returned by the API.

    Split from `Station` so the rich subclass can carry a `_client`
    reference without it leaking into the field-validation schema.
    """

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
        """Group the API's flat service/location fields into `services`/`location`.

        Several endpoints (e.g. `/system/.../stations`, `/market/{id}`)
        return service flags (`shipyard`, `outfitting`, ...) and location
        fields (`bodyId`, `latitude`, ...) at the top level of the payload
        rather than nested. This validator pulls them out into the
        `services`/`location` sub-objects before field validation runs.

        Args:
            data: The raw payload, or an already-validated `Station`/dict.

        Returns:
            `data` unchanged if it isn't a dict, otherwise `data` with the
            service/location keys moved under `services`/`location`.
        """
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
    """A station/market, with methods to traverse to its system and traded commodities."""

    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "Station":
        """Construct a `Station` from a JSON payload and attach the client.

        This is the only supported way to build a `Station`: constructing
        one via `model_validate` directly would leave `_client` unset,
        breaking every `get_*` method on the instance.

        Args:
            client: The shared `httpx.Client` to attach for further requests.
            payload: A single station object as returned by the API.

        Returns:
            The constructed, traversable `Station`.
        """
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_system(self)-> "System":
        """Fetch the system this station is located in.

        Returns:
            The containing `System`.
        """
        from .system import System

        logger.debug(f"GET /system/address/{self.system_address}")
        response = self._client.get(f"/system/address/{self.system_address}")
        system = response.json()
        return System.from_json(self._client, system)

    def get_full_details(self) -> "Station":
        """Ensure this station has its full service/location details loaded.

        Stations obtained from list endpoints (e.g. `System.get_stations`)
        already carry full detail. This is only needed for stations built
        from a sparser payload that lacks `location.body_id`; it re-fetches
        from `/market/{id}` and updates this instance in place.

        Returns:
            This `Station`, with `services`/`location` populated.
        """
        if self.location and self.location.body_id is not None:
            return self

        logger.debug(f"GET /market/{self.station_id}")
        response = self._client.get(f"/market/{self.station_id}")
        station_data = response.json()
        station = Station.from_json(self._client, station_data)
        self.__dict__.update(station.__dict__)
        return self

    def get_commodity_market(self, commodity: "Commodity") -> "CommodityMarket":
        """Fetch the buy/sell order for one commodity at this station.

        Args:
            commodity: The commodity to look up.

        Returns:
            The matching `CommodityMarket` entry.
        """
        from .market import CommodityMarket

        logger.debug(f"GET /market/{self.station_id}/commodity/name/{commodity.commodity_name}")
        response = self._client.get(f"/market/{self.station_id}/commodity/name/{commodity.commodity_name}")
        commodity_data = response.json()
        return CommodityMarket.from_json(self._client, commodity_data)

    def get_traded_commodities(self) -> list["CommodityMarket"]:
        """Fetch every buy/sell order at this station.

        Returns:
            One `CommodityMarket` entry per commodity traded at this station.
        """
        from .market import CommodityMarket

        logger.debug(f"GET /market/{self.station_id}/commodities")
        response = self._client.get(f"/market/{self.station_id}/commodities")
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [CommodityMarket.from_json(self._client, entry) for entry in commodities]
