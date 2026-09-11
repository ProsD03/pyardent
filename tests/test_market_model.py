"""Tests for CommodityMarket's traversal method (`get_station`) and
CommodityMarketData's bracket field quirks.

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

import respx
from httpx import Response

from pyardent import ArdentClient, CommodityMarket

MARKET_ENTRY = {
    "commodityName": "gold",
    "buyPrice": 44630,
    "demand": 0,
    "demandBracket": 0,
    "meanPrice": 40000,
    "sellPrice": 49027,
    "stock": 126303255,
    "stockBracket": 3,
    "updatedAt": "2026-06-16T08:33:50.000Z",
    "marketId": 128672445,
}

STATION_PAYLOAD = {
    "marketId": 128672445,
    "stationName": "Obsidian Orbital",
    "systemAddress": 8216113749,
    "updatedAt": "2026-06-18T00:03:37.482Z",
}


@respx.mock
def test_get_station_returns_station():
    client = ArdentClient()
    market = CommodityMarket.from_json(client._client, MARKET_ENTRY)

    respx.get("https://api.ardent-insight.com/v2/market/128672445").mock(
        return_value=Response(200, json=STATION_PAYLOAD)
    )

    station = market.get_station()

    assert station.station_id == 128672445
    assert station.station_name == "Obsidian Orbital"


# DEMAND_BRACKET / STOCK_BRACKET

def test_brackets_accept_ints():
    client = ArdentClient()
    market = CommodityMarket.from_json(client._client, MARKET_ENTRY)

    assert market.demand_bracket == 0
    assert market.stock_bracket == 3


def test_brackets_accept_empty_string():
    client = ArdentClient()
    payload = dict(MARKET_ENTRY, demandBracket="", stockBracket="")
    market = CommodityMarket.from_json(client._client, payload)

    assert market.demand_bracket == ""
    assert market.stock_bracket == ""
