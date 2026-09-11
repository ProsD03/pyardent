"""Tests for Station's traversal methods (`get_system`, `get_full_details`,
`get_commodity_market`, `get_traded_commodities`).

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

import respx
from httpx import Response

from pyardent import ArdentClient, Station, Commodity

# Has a bodyId, so already carries full location/service detail.
FULL_STATION = {
    "marketId": 128672445,
    "stationName": "Obsidian Orbital",
    "stationType": "Ocellus",
    "primaryEconomy": "HighTech",
    "secondaryEconomy": None,
    "shipyard": 1,
    "outfitting": 1,
    "systemAddress": 8216113749,
    "bodyId": 11326,
    "bodyName": "Maia A 2 a",
    "maxLandingPadSize": 3,
    "updatedAt": "2026-06-18T00:03:37.482Z",
}

# No bodyId - a sparser payload that requires get_full_details to re-fetch.
SPARSE_STATION = {
    "marketId": 128672445,
    "stationName": "Obsidian Orbital",
    "systemAddress": 8216113749,
}

SYSTEM_PAYLOAD = {
    "systemAddress": 8216113749,
    "systemName": "Maia",
    "systemX": -81.78125,
    "systemY": -149.4375,
    "systemZ": -343.375,
    "systemSector": "a1b2c3d4e5f6a7b8",
    "updatedAt": "2026-06-16T08:33:50.000Z",
}

GOLD = {
    "commodityName": "gold",
    "timestamp": "2025-05-08T09:20:08.043Z",
}

MARKET_ENTRY = {
    "commodityName": "gold",
    "buyPrice": 44630,
    "sellPrice": 49027,
    "marketId": 128672445,
    "updatedAt": "2026-06-16T08:33:50.000Z",
}


@respx.mock
def test_get_system_returns_system():
    client = ArdentClient()
    station = Station.from_json(client._client, FULL_STATION)

    respx.get("https://api.ardent-insight.com/v2/system/address/8216113749").mock(
        return_value=Response(200, json=SYSTEM_PAYLOAD)
    )

    system = station.get_system()

    assert system.system_name == "Maia"
    assert system.system_address == 8216113749


@respx.mock
def test_get_full_details_skips_request_when_already_detailed():
    client = ArdentClient()
    station = Station.from_json(client._client, FULL_STATION)

    # No route registered for GET /market/{id} - if get_full_details tried
    # to call it, respx would raise since this test is @respx.mock'd.
    result = station.get_full_details()

    assert result is station
    assert station.location is not None
    assert station.location.body_id == 11326


@respx.mock
def test_get_full_details_fetches_when_sparse():
    client = ArdentClient()
    station = Station.from_json(client._client, SPARSE_STATION)
    assert station.location is not None
    assert station.location.body_id is None

    respx.get("https://api.ardent-insight.com/v2/market/128672445").mock(
        return_value=Response(200, json=FULL_STATION)
    )

    result = station.get_full_details()

    assert result is station
    assert station.location.body_id == 11326
    assert station.services is not None
    assert station.services.shipyard is True


@respx.mock
def test_get_commodity_market_returns_commodity_market():
    client = ArdentClient()
    station = Station.from_json(client._client, FULL_STATION)
    commodity = Commodity.from_json(client._client, GOLD)

    respx.get("https://api.ardent-insight.com/v2/market/128672445/commodity/name/gold").mock(
        return_value=Response(200, json=MARKET_ENTRY)
    )

    market = station.get_commodity_market(commodity)

    assert market.commodity_name == "gold"
    assert market.sell_price == 49027


@respx.mock
def test_get_traded_commodities_returns_commodity_markets():
    client = ArdentClient()
    station = Station.from_json(client._client, FULL_STATION)

    respx.get("https://api.ardent-insight.com/v2/market/128672445/commodities").mock(
        return_value=Response(200, json=[MARKET_ENTRY])
    )

    markets = station.get_traded_commodities()

    assert len(markets) == 1
    assert markets[0].commodity_name == "gold"
