"""Tests for Commodity's traversal methods (`get_rare_station`, the
import/export lookups, and the system/station market lookups).

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

import pytest
import respx
from httpx import Response

from pyardent import ArdentClient, Commodity, System, Station

GOLD = {
    "commodityName": "gold",
    "timestamp": "2025-05-08T09:20:08.043Z",
}

RARE_COMMODITY = {
    "commodityName": "leestianeviljuice",
    "rare": True,
    "rareMarketId": 128672445,
    "rareMaxCount": 10,
    "timestamp": "2025-05-08T09:20:08.043Z",
}

RARE_COMMODITY_NO_STATION = {
    "commodityName": "leestianeviljuice",
    "rare": True,
    "timestamp": "2025-05-08T09:20:08.043Z",
}

RARE_STATION_PAYLOAD = {
    "marketId": 128672445,
    "stationName": "Leesti Trading Post",
    "systemAddress": 3107509474578,
    "updatedAt": "2026-06-18T00:03:37.482Z",
}

MARKET_ENTRY = {
    "commodityName": "gold",
    "buyPrice": 44630,
    "sellPrice": 49027,
    "marketId": 128672445,
    "updatedAt": "2026-06-16T08:33:50.000Z",
}

SOL_PAYLOAD = {
    "systemAddress": 10477373803,
    "systemName": "Sol",
    "systemX": 0,
    "systemY": 0,
    "systemZ": 0,
    "systemSector": "a1b2c3d4e5f6a7b8",
    "updatedAt": "2026-06-16T08:33:50.000Z",
}

STATION_PAYLOAD = {
    "marketId": 128672445,
    "stationName": "Abraham Lincoln",
    "systemAddress": 10477373803,
    "updatedAt": "2026-06-18T00:03:37.482Z",
}


def _commodity(payload: dict = GOLD) -> Commodity:
    client = ArdentClient()
    return Commodity.from_json(client._client, payload)


def _commodity_and_system() -> tuple[Commodity, System]:
    client = ArdentClient()
    commodity = Commodity.from_json(client._client, GOLD)
    system = System.from_json(client._client, SOL_PAYLOAD)
    return commodity, system


def _commodity_and_station() -> tuple[Commodity, Station]:
    client = ArdentClient()
    commodity = Commodity.from_json(client._client, GOLD)
    station = Station.from_json(client._client, dict(STATION_PAYLOAD))
    return commodity, station


# GET_RARE_STATION

@respx.mock
def test_get_rare_station_returns_station():
    commodity = _commodity(RARE_COMMODITY)

    respx.get("https://api.ardent-insight.com/v2/market/128672445").mock(
        return_value=Response(200, json=RARE_STATION_PAYLOAD)
    )

    station = commodity.get_rare_station()

    assert station is not None
    assert station.station_name == "Leesti Trading Post"


@respx.mock
def test_get_rare_station_returns_none_when_not_rare():
    commodity = _commodity(GOLD)

    # No route registered - if get_rare_station made a request, respx would
    # raise since this test is @respx.mock'd.
    assert commodity.get_rare_station() is None


@respx.mock
def test_get_rare_station_returns_none_when_no_station_recorded():
    commodity = _commodity(RARE_COMMODITY_NO_STATION)

    assert commodity.get_rare_station() is None


# GET_IMPORTERS

@respx.mock
def test_get_importers_returns_commodity_markets():
    commodity = _commodity()

    route = respx.get("https://api.ardent-insight.com/v2/commodity/name/gold/imports").mock(
        return_value=Response(200, json=[MARKET_ENTRY])
    )

    importers = commodity.get_importers(min_volume=5, min_price=10)

    assert route.calls.last.request.url.params["minVolume"] == "5"
    assert route.calls.last.request.url.params["minPrice"] == "10"
    assert len(importers) == 1


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"min_price": -1},
    {"max_days_ago": -1},
])
def test_get_importers_raises_on_negative_params(kwargs):
    commodity = _commodity()

    with pytest.raises(ValueError):
        commodity.get_importers(**kwargs)


# GET_EXPORTERS

@respx.mock
def test_get_exporters_omits_max_price_when_not_given():
    commodity = _commodity()

    route = respx.get("https://api.ardent-insight.com/v2/commodity/name/gold/exports").mock(
        return_value=Response(200, json=[MARKET_ENTRY])
    )

    exporters = commodity.get_exporters()

    assert "maxPrice" not in route.calls.last.request.url.params
    assert len(exporters) == 1


@respx.mock
def test_get_exporters_includes_max_price_when_given():
    commodity = _commodity()

    route = respx.get("https://api.ardent-insight.com/v2/commodity/name/gold/exports").mock(
        return_value=Response(200, json=[MARKET_ENTRY])
    )

    commodity.get_exporters(max_price=1000)

    assert route.calls.last.request.url.params["maxPrice"] == "1000"


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"max_price": -1},
    {"max_days_ago": -1},
])
def test_get_exporters_raises_on_negative_params(kwargs):
    commodity = _commodity()

    with pytest.raises(ValueError):
        commodity.get_exporters(**kwargs)


# GET_SYSTEM_MARKET

@respx.mock
def test_get_system_market_returns_commodity_markets():
    commodity, system = _commodity_and_system()

    respx.get("https://api.ardent-insight.com/v2/system/address/10477373803/commodity/name/gold").mock(
        return_value=Response(200, json=[MARKET_ENTRY])
    )

    markets = commodity.get_system_market(system)

    assert len(markets) == 1


def test_get_system_market_raises_on_negative_max_days_ago():
    commodity, system = _commodity_and_system()

    with pytest.raises(ValueError):
        commodity.get_system_market(system, max_days_ago=-1)


# GET_NEARBY_IMPORTERS

@respx.mock
def test_get_nearby_importers_returns_commodity_markets():
    commodity, system = _commodity_and_system()

    respx.get(
        "https://api.ardent-insight.com/v2/system/address/10477373803/commodity/name/gold/nearby/imports"
    ).mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = commodity.get_nearby_importers(system)

    assert len(markets) == 1


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"min_price": -1},
    {"max_distance": -1},
    {"max_distance": 501},
    {"max_days_ago": -1},
])
def test_get_nearby_importers_raises_on_invalid_params(kwargs):
    commodity, system = _commodity_and_system()

    with pytest.raises(ValueError):
        commodity.get_nearby_importers(system, **kwargs)


# GET_NEARBY_EXPORTERS

@respx.mock
def test_get_nearby_exporters_omits_max_price_when_not_given():
    commodity, system = _commodity_and_system()

    route = respx.get(
        "https://api.ardent-insight.com/v2/system/address/10477373803/commodity/name/gold/nearby/exports"
    ).mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = commodity.get_nearby_exporters(system)

    assert "maxPrice" not in route.calls.last.request.url.params
    assert len(markets) == 1


@respx.mock
def test_get_nearby_exporters_includes_max_price_when_given():
    commodity, system = _commodity_and_system()

    route = respx.get(
        "https://api.ardent-insight.com/v2/system/address/10477373803/commodity/name/gold/nearby/exports"
    ).mock(return_value=Response(200, json=[MARKET_ENTRY]))

    commodity.get_nearby_exporters(system, max_price=1000)

    assert route.calls.last.request.url.params["maxPrice"] == "1000"


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"max_price": -1},
    {"max_distance": -1},
    {"max_distance": 501},
    {"max_days_ago": -1},
])
def test_get_nearby_exporters_raises_on_invalid_params(kwargs):
    commodity, system = _commodity_and_system()

    with pytest.raises(ValueError):
        commodity.get_nearby_exporters(system, **kwargs)


# GET_STATION_MARKET

@respx.mock
def test_get_station_market_returns_commodity_market():
    commodity, station = _commodity_and_station()

    respx.get("https://api.ardent-insight.com/v2/market/128672445/commodity/name/gold").mock(
        return_value=Response(200, json=MARKET_ENTRY)
    )

    market = commodity.get_station_market(station)

    assert market.commodity_name == "gold"
    assert market.sell_price == 49027
