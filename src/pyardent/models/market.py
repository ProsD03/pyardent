"""Model for a single commodity buy/sell order at a market.

`CommodityMarket` is the common return type for nearly every trade-related
endpoint in this library (`System`/`Commodity`/`Station` import and export
lookups) since the API returns this same shape across all of them.
"""

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
    """Plain fields of a single commodity order at a market, as returned by the API.

    `buy_price` is what you pay to buy from this station (i.e. it's
    exporting); `sell_price` is what this station pays you to sell to it
    (i.e. it's importing). `demand_bracket`/`stock_bracket` are the game's
    coarse low/medium/high indicators (0-3); the API occasionally returns an
    empty string instead of an int for these, hence the `int | str` type.

    Split from `CommodityMarket` so the rich subclass can carry a `_client`
    reference without it leaking into the field-validation schema.
    """

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
    """A single commodity's buy/sell order at one market, with a method to traverse to its station."""

    _client: httpx.Client = PrivateAttr()

    @classmethod
    def from_json(cls, client: httpx.Client, payload: dict) -> "CommodityMarket":
        """Construct a `CommodityMarket` from a JSON payload and attach the client.

        This is the only supported way to build a `CommodityMarket`:
        constructing one via `model_validate` directly would leave `_client`
        unset, breaking `get_station`.

        Args:
            client: The shared `httpx.Client` to attach for further requests.
            payload: A single commodity-order object as returned by the API.

        Returns:
            The constructed, traversable `CommodityMarket`.
        """
        instance = cls.model_validate(payload)
        instance._client = client
        return instance

    def get_station(self) -> "Station":
        """Fetch the station this order belongs to.

        Returns:
            The `Station` identified by `station_id`.
        """
        from .station import Station
        logger.debug(f"GET /market/{self.station_id}")
        response = self._client.get(f"/market/{self.station_id}")
        station = response.json()
        return Station.from_json(self._client, station)
