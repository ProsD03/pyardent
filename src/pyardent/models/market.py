import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import BaseModel, PrivateAttr, ConfigDict, Field
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from .station import Station

logger = logging.getLogger("pyardent.models.market")

class CommodityMarketData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    commodity_name: str | None = None
    buy_price: int | None = None
    demand: int | None = None
    demand_bracket: int | str | None = None
    mean_price: int | None = None
    sell_price: int | None = None
    stock: int | None = None
    stock_bracket: int | str | None = None
    updated_at: datetime | None = None

    station_id: int | None = Field(alias="marketId", default=None)

class CommodityMarket(CommodityMarketData):
    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "CommodityMarket":
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_station(self) -> "Station":
        from .station import Station
        logger.debug(f"GET /market/{self.station_id}")
        response = self._client.get(f"/market/{self.station_id}")
        system = response.json()
        return Station.from_json(self._client, system)
