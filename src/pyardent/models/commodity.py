import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, ConfigDict, PrivateAttr, Field
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from .station import Station

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
        system = response.json()
        return Station.from_json(self._client, system)