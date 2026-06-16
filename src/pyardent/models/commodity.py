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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    commodity_name: str
    rare: bool = False
    rare_station_id: int | None = Field(alias="rareMarketId", default=None)
    rare_max_count: int | None = None
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
    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "Commodity":
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_rare_station(self) -> "Station | None":
        if not self.rare or self.rare_station_id is None:
            return None

        from .station import Station
        logger.debug(f"GET /market/{self.rare_station_id}")
        response = self._client.get(f"/market/{self.rare_station_id}")
        station = response.json()
        return Station.from_json(self._client, station)

    def get_importers(self, min_volume: int = 1, min_price: int = 1, fleet_carriers: bool | None = None, max_days_ago: int = 30) -> list["CommodityMarket"]:
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