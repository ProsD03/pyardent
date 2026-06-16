"""Models for the API's system resource (`/system/...`).

`System` is a graph-traversal node, not a flat DTO: every `get_*` method
makes a further API call rooted at `self.system_address` and returns other
rich models (`Station`, `CommodityMarket`, `System`).
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, PrivateAttr, ConfigDict
from pydantic.alias_generators import to_camel

from ..types import StationServices, LandingPad

if TYPE_CHECKING:
    from .station import Station
    from .market import CommodityMarket
    from .commodity import Commodity

logger = logging.getLogger("pyardent.models.system")

class SystemData(BaseModel):
    """Plain fields of a system, as returned by the API.

    Split from `System` so the rich subclass can carry a `_client` reference
    without it leaking into the field-validation schema.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system_address: int
    system_name: str
    system_x: float
    system_y: float
    system_z: float
    system_sector: str
    updated_at: datetime
    disambiguation: list["System"] | None = None
    """Other systems sharing this exact name, if any. Only ever populated on
    the result of `SystemModule.get_by_name`/`get_by_address`; the API
    includes this as a hint when a name lookup happens to be ambiguous."""

class System(SystemData):
    """A star system, with methods to traverse to its stations, nearby systems, and traded commodities."""

    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "System":
        """Construct a `System` from a JSON payload and attach the client.

        This is the only supported way to build a `System`: constructing one
        via `model_validate` directly would leave `_client` unset, breaking
        every `get_*` method on the instance (and on any nested
        `disambiguation` entries, whose `_client` is also set here).

        Args:
            client: The shared `httpx.Client` to attach for further requests.
            payload: A single system object as returned by the API.

        Returns:
            The constructed, traversable `System`.
        """
        instance = cls.model_validate(payload)
        instance._client = client
        if instance.disambiguation:
            for candidate in instance.disambiguation:
                candidate._client = client
            logger.warning(
                f"System name '{instance.system_name}' is ambiguous: "
                f"{len(instance.disambiguation)} other system(s) share this name"
            )
        return instance

    def get_stations(self) -> list["Station"]:
        """Fetch all known dockable stations in this system.

        Returns:
            Stations in this system, in the order returned by the API.
        """
        from .station import Station

        logger.debug(f"GET /system/address/{self.system_address}/stations")
        response = self._client.get(f"/system/address/{self.system_address}/stations")
        stations = response.json()
        logger.debug(f"Parsing {len(stations)} stations")
        return [Station.from_json(self._client, station) for station in stations]

    def get_nearby_systems(self, max_distance: int = 100, hide_debug_system: bool = True) -> list["System"]:
        """Fetch systems near this one, ordered by distance.

        Args:
            max_distance: Search radius in light-years. Must be between 0
                and 500 (the API's own cap).
            hide_debug_system: If True (default), filter out "TestRender",
                an internal test system that otherwise shows up in results.

        Returns:
            Up to 1000 nearby systems, closest first.

        Raises:
            ValueError: If `max_distance` is outside `[0, 500]`.
        """
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
        """Find the nearest stations offering a given service.

        Args:
            service: The station service to search for.
            min_landing_pad_size: If given, only return stations with at
                least this landing pad size.

        Returns:
            Up to 20 matching stations, closest first.
        """
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

    def get_traded_commodities(self) -> list["CommodityMarket"]:
        """Fetch all known trade orders (buy and sell) across every station in this system.

        Returns:
            One `CommodityMarket` entry per commodity per station.
        """
        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{self.system_address}/commodities")
        response = self._client.get(f"/system/address/{self.system_address}/commodities")
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, commodity) for commodity in commodities
        ]

    def get_imported_commodities(self,  min_volume: int = 1, min_price: int = 1, fleet_carriers: bool | None = None, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch commodities this system imports — places you can sell to.

        Args:
            min_volume: Minimum demand to include. Demand of 0 means
                infinite demand and is always included.
            min_price: Minimum sell price to include.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            Matching import orders, one `CommodityMarket` entry per
            commodity per station.

        Raises:
            ValueError: If `min_volume`, `min_price`, or `max_days_ago` is negative.
        """
        if min_volume < 0:
            raise ValueError(f"min_volume cannot be negative. received: {min_volume}")
        if min_price < 0:
            raise ValueError(f"min_price cannot be negative. received: {min_price}")
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")


        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{self.system_address}/commodities/imports")
        response = self._client.get(f"/system/address/{self.system_address}/commodities/imports", params={
            "minVolume": min_volume,
            "minPrice": min_price,
            "fleetCarriers": fleet_carriers,
            "maxDaysAgo": max_days_ago,
        })
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, commodity) for commodity in commodities
        ]

    def get_exported_commodities(self, min_volume: int = 1, max_price: int | None = None, fleet_carriers: bool | None = None, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch commodities this system exports — places you can buy from.

        Args:
            min_volume: Minimum stock to include.
            max_price: If given, exclude entries with a buy price above this.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            Matching export orders, one `CommodityMarket` entry per
            commodity per station.

        Raises:
            ValueError: If `min_volume`, `max_price`, or `max_days_ago` is negative.
        """
        if min_volume < 0:
            raise ValueError(f"min_volume cannot be negative. received: {min_volume}")
        if max_price and max_price < 0:
            raise ValueError(f"max_price cannot be negative. received: {max_price}")
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")

        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{self.system_address}/commodities/exports")
        if max_price is None:
            params = {
            "minVolume": min_volume,
            "fleetCarriers": fleet_carriers,
            "maxDaysAgo": max_days_ago,
        }
        else:
            params = {
                "minVolume": min_volume,
                "maxPrice": max_price,
                "fleetCarriers": fleet_carriers,
                "maxDaysAgo": max_days_ago,
            }
        response = self._client.get(f"/system/address/{self.system_address}/commodities/exports", params=params)
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, commodity) for commodity in commodities
        ]

    def get_commodity_market(self, commodity: "Commodity", max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch all buy/sell orders for one commodity across stations in this system.

        Args:
            commodity: The commodity to look up.
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            One `CommodityMarket` entry per station in this system trading
            `commodity` (empty if none do).

        Raises:
            ValueError: If `max_days_ago` is negative.
        """
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")

        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{self.system_address}/commodity/name/{commodity.commodity_name}")
        response = self._client.get(f"/system/address/{self.system_address}/commodity/name/{commodity.commodity_name}", params={
            "maxDaysAgo": max_days_ago,
        })
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, entry) for entry in commodities
        ]

    def get_nearby_importers(self, commodity: "Commodity", min_volume: int = 1, min_price: int = 1, fleet_carriers: bool | None = None, max_distance: int = 100, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch nearby places importing a commodity — places you can sell to near this system.

        Args:
            commodity: The commodity to look up.
            min_volume: Minimum demand to include. Demand of 0 means
                infinite demand and is always included.
            min_price: Minimum sell price to include.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_distance: Search radius in light-years from this system.
                Must be between 0 and 500 (the API's own cap).
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            Up to 1000 matching import orders, ordered by highest price
            (the best place to sell first).

        Raises:
            ValueError: If `min_volume` or `min_price` is negative, if
                `max_distance` is outside `[0, 500]`, or if `max_days_ago`
                is negative.
        """
        if min_volume < 0:
            raise ValueError(f"min_volume cannot be negative. received: {min_volume}")
        if min_price < 0:
            raise ValueError(f"min_price cannot be negative. received: {min_price}")
        if max_distance < 0 or max_distance > 500:
            raise ValueError(f"max_distance cannot be negative or greater than 500. received: {max_distance}")
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")

        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{self.system_address}/commodity/name/{commodity.commodity_name}/nearby/imports")
        response = self._client.get(f"/system/address/{self.system_address}/commodity/name/{commodity.commodity_name}/nearby/imports",
                                    params={
                                        "minVolume": min_volume,
                                        "minPrice": min_price,
                                        "fleetCarriers": fleet_carriers,
                                        "maxDistance": max_distance,
                                        "maxDaysAgo": max_days_ago,
                                    })
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, entry) for entry in commodities
        ]

    def get_nearby_exporters(self, commodity: "Commodity", min_volume: int = 1, max_price: int | None = None, fleet_carriers: bool | None = None, max_distance: int = 100, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch nearby places exporting a commodity — places you can buy from near this system.

        Args:
            commodity: The commodity to look up.
            min_volume: Minimum stock to include.
            max_price: If given, exclude entries with a buy price above this.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_distance: Search radius in light-years from this system.
                Must be between 0 and 500 (the API's own cap).
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            Up to 1000 matching export orders, ordered by lowest price
            (the best place to buy first).

        Raises:
            ValueError: If `min_volume` or `max_price` is negative, if
                `max_distance` is outside `[0, 500]`, or if `max_days_ago`
                is negative.
        """
        if min_volume < 0:
            raise ValueError(f"min_volume cannot be negative. received: {min_volume}")
        if max_price and max_price < 0:
            raise ValueError(f"max_price cannot be negative. received: {max_price}")
        if max_distance < 0 or max_distance > 500:
            raise ValueError(f"max_distance cannot be negative or greater than 500. received: {max_distance}")
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")

        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{self.system_address}/commodity/name/{commodity.commodity_name}/nearby/exports")
        if max_price is None:
            params = {
                "minVolume": min_volume,
                "fleetCarriers": fleet_carriers,
                "maxDaysAgo": max_days_ago,
            }
        else:
            params = {
                "minVolume": min_volume,
                "maxPrice": max_price,
                "fleetCarriers": fleet_carriers,
                "maxDaysAgo": max_days_ago,
            }

        response = self._client.get(
            f"/system/address/{self.system_address}/commodity/name/{commodity.commodity_name}/nearby/exports",
            params=params)
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, entry) for entry in commodities
        ]
