import logging
from datetime import datetime

import httpx
from pydantic import BaseModel, ConfigDict, PrivateAttr
from pydantic.alias_generators import to_camel

logger = logging.getLogger("pyardent.models.commodity")

class CommodityData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    commodity_name: str
    rare: bool = False
    rare_market_id: int | None = None
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