"""Models for the API's commodity resource (`/commodity/...`).

`Commodity` is a graph-traversal node, not a flat DTO: every `get_*` method
makes a further API call rooted at `self.commodity_name` and returns other
rich models (`Station`, `CommodityMarket`).
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, ConfigDict, PrivateAttr, Field
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from .station import Station
    from .market import CommodityMarket
    from .system import System

logger = logging.getLogger("pyardent.models.commodity")

class CommodityData(BaseModel):
    """Plain fields of a commodity summary report, as returned by the API.

    The `min`/`max`/`avg`/`total` price and stock/demand fields are
    aggregates across every known market, excluding fleet carriers. Split
    from `Commodity` so the rich subclass can carry a `_client` reference
    without it leaking into the field-validation schema.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    commodity_name: str
    rare: bool = False
    rare_station_id: int | None = Field(alias="rareMarketId", default=None)
    rare_max_count: int | None = None
    """For rare commodities, the cargo quantity threshold beyond which
    selling more at once starts degrading the price."""
    min_buy_price: int | None = None
    max_buy_price: int | None = None
    avg_buy_price: int | None = None
    total_stock: int | None = None
    min_sell_price: int | None = None
    max_sell_price: int | None = None
    avg_sell_price: int | None = None
    total_demand: int | None = None
    timestamp: datetime

class Commodity(CommodityData):
    """A tradeable commodity, with methods to find where it's bought, sold, or made."""

    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "Commodity":
        """Construct a `Commodity` from a JSON payload and attach the client.

        This is the only supported way to build a `Commodity`: constructing
        one via `model_validate` directly would leave `_client` unset,
        breaking every `get_*` method on the instance.

        Args:
            client: The shared `httpx.Client` to attach for further requests.
            payload: A single commodity object as returned by the API.

        Returns:
            The constructed, traversable `Commodity`.
        """
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_rare_station(self) -> "Station | None":
        """Fetch the station where this rare commodity is sold, if it is one.

        Returns:
            The rare commodity's home station, or None if this commodity
            isn't rare (or has no recorded home station).
        """
        if not self.rare or self.rare_station_id is None:
            return None

        from .station import Station
        logger.debug(f"GET /market/{self.rare_station_id}")
        response = self._client.get(f"/market/{self.rare_station_id}")
        station = response.json()
        return Station.from_json(self._client, station)

    def get_importers(self, min_volume: int = 1, min_price: int = 1, fleet_carriers: bool | None = None, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch places importing this commodity — places you can sell to.

        Args:
            min_volume: Minimum demand to include. Demand of 0 means
                infinite demand and is always included.
            min_price: Minimum sell price to include.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            Up to 100 matching import orders, ordered by highest price
            (the best place to sell first).

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
        logger.debug(f"GET /commodity/name/{self.commodity_name}/imports")

        response = self._client.get(f"/commodity/name/{self.commodity_name}/imports", params={
            "minVolume": min_volume,
            "minPrice": min_price,
            "fleetCarriers": fleet_carriers,
            "maxDaysAgo": max_days_ago,
        })
        importers = response.json()
        logger.debug(f"Parsing {len(importers)} importers")
        return [CommodityMarket.from_json(self._client, importer) for importer in importers]

    def get_exporters(self, min_volume: int = 1, max_price: int | None = None, fleet_carriers: bool | None = None, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch places exporting this commodity — places you can buy from.

        Args:
            min_volume: Minimum stock to include.
            max_price: If given, exclude entries with a buy price above this.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            Up to 100 matching export orders, ordered by lowest price
            (the best place to buy first).

        Raises:
            ValueError: If `min_volume` or `max_price` is negative, or if
                `max_days_ago` is negative.
        """
        if min_volume < 0:
            raise ValueError(f"min_volume cannot be negative. received: {min_volume}")
        if max_price and max_price < 0:
            raise ValueError(f"max_price cannot be negative. received: {max_price}")
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")

        from .market import CommodityMarket
        logger.debug(f"GET /commodity/name/{self.commodity_name}/exports")
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
        response = self._client.get(f"/commodity/name/{self.commodity_name}/exports", params=params)
        exporters = response.json()
        logger.debug(f"Parsing {len(exporters)} exporters")
        return [CommodityMarket.from_json(self._client, exporter) for exporter in exporters]

    def get_system_market(self, system: "System", max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch all buy/sell orders for this commodity across stations in a system.

        Args:
            system: The system to look up.
            max_days_ago: Exclude trade data older than this many days.

        Returns:
            One `CommodityMarket` entry per station in `system` trading this
            commodity (empty if none do).

        Raises:
            ValueError: If `max_days_ago` is negative.
        """
        if max_days_ago < 0:
            raise ValueError(f"max_days_ago cannot be negative. received: {max_days_ago}")

        from .market import CommodityMarket
        logger.debug(f"GET /system/address/{system.system_address}/commodity/name/{self.commodity_name}")
        response = self._client.get(f"/system/address/{system.system_address}/commodity/name/{self.commodity_name}", params={
            "maxDaysAgo": max_days_ago,
        })
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, entry) for entry in commodities
        ]

    def get_nearby_importers(self, system: "System", min_volume: int = 1, min_price: int = 1, fleet_carriers: bool | None = None, max_distance: int = 100, max_days_ago: int = 30) -> list["CommodityMarket"]:
        """Fetch nearby places importing this commodity — places you can sell to near a system.

        Args:
            system: The system to search around.
            min_volume: Minimum demand to include. Demand of 0 means
                infinite demand and is always included.
            min_price: Minimum sell price to include.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_distance: Search radius in light-years from `system`. Must
                be between 0 and 500 (the API's own cap).
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
        logger.debug(f"GET /system/address/{system.system_address}/commodity/name/{self.commodity_name}/nearby/imports")
        response = self._client.get(f"/system/address/{system.system_address}/commodity/name/{self.commodity_name}/nearby/imports",
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

    def get_nearby_exporters(self, system: "System", min_volume: int = 1, max_price: int | None = None,
                             fleet_carriers: bool | None = None, max_distance: int = 100, max_days_ago: int = 30) -> \
    list["CommodityMarket"]:
        """Fetch nearby places exporting this commodity — places you can buy from near a system.

        Args:
            system: The system to search around.
            min_volume: Minimum stock to include.
            max_price: If given, exclude entries with a buy price above this.
            fleet_carriers: If True, only fleet carriers; if False, exclude
                them; if None (default), include all station types.
            max_distance: Search radius in light-years from `system`. Must
                be between 0 and 500 (the API's own cap).
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
        logger.debug(f"GET /system/address/{system.system_address}/commodity/name/{self.commodity_name}/nearby/exports")
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
            f"/system/address/{system.system_address}/commodity/name/{self.commodity_name}/nearby/exports",
            params=params)
        commodities = response.json()
        logger.debug(f"Parsing {len(commodities)} commodities")
        return [
            CommodityMarket.from_json(self._client, entry) for entry in commodities
        ]

    def get_station_market(self, station: "Station") -> "CommodityMarket":
        """Fetch the buy/sell order for this commodity at one specific station.

        Args:
            station: The station to look up.

        Returns:
            The matching `CommodityMarket` entry.
        """
        from .market import CommodityMarket
        logger.debug(f"GET /market/{station.station_id}/commodity/name/{self.commodity_name}")
        response = self._client.get(f"/market/{station.station_id}/commodity/name/{self.commodity_name}")
        commodity = response.json()
        return CommodityMarket.from_json(self._client, commodity)