"""Tests for System's traversal methods (`get_stations`, `get_nearby_systems`,
`get_nearest_service`, and the commodity-market lookups).

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

import pytest
import respx
from httpx import Response

from pyardent import ArdentClient, System, Commodity, StationServices, LandingPad

BASE = "https://api.ardent-insight.com/v2/system/address/10477373803"

SOL_PAYLOAD = {
    "systemAddress": 10477373803,
    "systemName": "Sol",
    "systemX": 0,
    "systemY": 0,
    "systemZ": 0,
    "systemSector": "a1b2c3d4e5f6a7b8",
    "updatedAt": "2026-06-16T08:33:50.000Z",
}

ALPHA_CENTAURI_PAYLOAD = {
    "systemAddress": 3932277478106,
    "systemName": "Alpha Centauri",
    "systemX": 3.03125,
    "systemY": -0.09375,
    "systemZ": 3.15625,
    "systemSector": "a1b2c3d4e5f6a7b8",
    "updatedAt": "2026-06-16T08:33:50.000Z",
}

TESTRENDER_PAYLOAD = {
    "systemAddress": 1,
    "systemName": "TestRender",
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


def _system() -> System:
    client = ArdentClient()
    return System.from_json(client._client, SOL_PAYLOAD)


def _system_and_commodity() -> tuple[System, Commodity]:
    client = ArdentClient()
    system = System.from_json(client._client, SOL_PAYLOAD)
    commodity = Commodity.from_json(client._client, GOLD)
    return system, commodity


# GET_STATIONS

@respx.mock
def test_get_stations_returns_stations():
    system = _system()

    respx.get(f"{BASE}/stations").mock(return_value=Response(200, json=[STATION_PAYLOAD]))

    stations = system.get_stations()

    assert len(stations) == 1
    assert stations[0].station_name == "Abraham Lincoln"


# GET_NEARBY_SYSTEMS

@respx.mock
def test_get_nearby_systems_filters_debug_system_by_default():
    system = _system()

    respx.get(f"{BASE}/nearby").mock(
        return_value=Response(200, json=[ALPHA_CENTAURI_PAYLOAD, TESTRENDER_PAYLOAD])
    )

    nearby = system.get_nearby_systems()

    assert len(nearby) == 1
    assert nearby[0].system_name == "Alpha Centauri"


@respx.mock
def test_get_nearby_systems_includes_debug_system_when_requested():
    system = _system()

    respx.get(f"{BASE}/nearby").mock(
        return_value=Response(200, json=[ALPHA_CENTAURI_PAYLOAD, TESTRENDER_PAYLOAD])
    )

    nearby = system.get_nearby_systems(hide_debug_system=False)

    assert len(nearby) == 2


@pytest.mark.parametrize("max_distance", [-1, 501])
def test_get_nearby_systems_raises_on_invalid_max_distance(max_distance):
    system = _system()

    with pytest.raises(ValueError):
        system.get_nearby_systems(max_distance=max_distance)


# GET_NEAREST_SERVICE

@respx.mock
def test_get_nearest_service_returns_stations():
    system = _system()

    route = respx.get(f"{BASE}/nearest/shipyard").mock(return_value=Response(200, json=[STATION_PAYLOAD]))

    stations = system.get_nearest_service(StationServices.SHIPYARD)

    assert route.called
    assert "minLandingPadSize" not in route.calls.last.request.url.params
    assert len(stations) == 1


@respx.mock
def test_get_nearest_service_includes_min_landing_pad_size_param():
    system = _system()

    route = respx.get(f"{BASE}/nearest/shipyard").mock(return_value=Response(200, json=[STATION_PAYLOAD]))

    system.get_nearest_service(StationServices.SHIPYARD, min_landing_pad_size=LandingPad.LARGE)

    assert route.calls.last.request.url.params["minLandingPadSize"] == "3"


# GET_TRADED_COMMODITIES

@respx.mock
def test_get_traded_commodities_returns_commodity_markets():
    system = _system()

    respx.get(f"{BASE}/commodities").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = system.get_traded_commodities()

    assert len(markets) == 1
    assert markets[0].commodity_name == "gold"


# GET_IMPORTED_COMMODITIES

@respx.mock
def test_get_imported_commodities_returns_commodity_markets():
    system = _system()

    route = respx.get(f"{BASE}/commodities/imports").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = system.get_imported_commodities(min_volume=5, min_price=10)

    assert route.calls.last.request.url.params["minVolume"] == "5"
    assert route.calls.last.request.url.params["minPrice"] == "10"
    assert len(markets) == 1


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"min_price": -1},
    {"max_days_ago": -1},
])
def test_get_imported_commodities_raises_on_negative_params(kwargs):
    system = _system()

    with pytest.raises(ValueError):
        system.get_imported_commodities(**kwargs)


# GET_EXPORTED_COMMODITIES

@respx.mock
def test_get_exported_commodities_omits_max_price_when_not_given():
    system = _system()

    route = respx.get(f"{BASE}/commodities/exports").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    system.get_exported_commodities()

    assert "maxPrice" not in route.calls.last.request.url.params


@respx.mock
def test_get_exported_commodities_includes_max_price_when_given():
    system = _system()

    route = respx.get(f"{BASE}/commodities/exports").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = system.get_exported_commodities(max_price=1000)

    assert route.calls.last.request.url.params["maxPrice"] == "1000"
    assert len(markets) == 1


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"max_price": -1},
    {"max_days_ago": -1},
])
def test_get_exported_commodities_raises_on_negative_params(kwargs):
    system = _system()

    with pytest.raises(ValueError):
        system.get_exported_commodities(**kwargs)


# GET_COMMODITY_MARKET

@respx.mock
def test_get_commodity_market_returns_commodity_markets():
    system, commodity = _system_and_commodity()

    respx.get(f"{BASE}/commodity/name/gold").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = system.get_commodity_market(commodity)

    assert len(markets) == 1
    assert markets[0].commodity_name == "gold"


def test_get_commodity_market_raises_on_negative_max_days_ago():
    system, commodity = _system_and_commodity()

    with pytest.raises(ValueError):
        system.get_commodity_market(commodity, max_days_ago=-1)


# GET_NEARBY_IMPORTERS

@respx.mock
def test_get_nearby_importers_returns_commodity_markets():
    system, commodity = _system_and_commodity()

    respx.get(f"{BASE}/commodity/name/gold/nearby/imports").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = system.get_nearby_importers(commodity)

    assert len(markets) == 1


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"min_price": -1},
    {"max_distance": -1},
    {"max_distance": 501},
    {"max_days_ago": -1},
])
def test_get_nearby_importers_raises_on_invalid_params(kwargs):
    system, commodity = _system_and_commodity()

    with pytest.raises(ValueError):
        system.get_nearby_importers(commodity, **kwargs)


# GET_NEARBY_EXPORTERS

@respx.mock
def test_get_nearby_exporters_omits_max_price_when_not_given():
    system, commodity = _system_and_commodity()

    route = respx.get(f"{BASE}/commodity/name/gold/nearby/exports").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    markets = system.get_nearby_exporters(commodity)

    assert "maxPrice" not in route.calls.last.request.url.params
    assert len(markets) == 1


@respx.mock
def test_get_nearby_exporters_includes_max_price_when_given():
    system, commodity = _system_and_commodity()

    route = respx.get(f"{BASE}/commodity/name/gold/nearby/exports").mock(return_value=Response(200, json=[MARKET_ENTRY]))

    system.get_nearby_exporters(commodity, max_price=1000)

    assert route.calls.last.request.url.params["maxPrice"] == "1000"


@pytest.mark.parametrize("kwargs", [
    {"min_volume": -1},
    {"max_price": -1},
    {"max_distance": -1},
    {"max_distance": 501},
    {"max_days_ago": -1},
])
def test_get_nearby_exporters_raises_on_invalid_params(kwargs):
    system, commodity = _system_and_commodity()

    with pytest.raises(ValueError):
        system.get_nearby_exporters(commodity, **kwargs)
