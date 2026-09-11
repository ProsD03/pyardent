"""Tests for MetaModule (`/version`, `/stats`, `/stats/stations/*`).

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

import respx
from httpx import Response

from pyardent import ArdentClient

VERSION_PAYLOAD = {"version": "2.4.1"}

STATS_PAYLOAD = {
    "systems": 132456,
    "pointsOfInterest": 987,
    "stations": {
        "stations": 45678,
        "carriers": 1234,
        "updatedInLast24Hours": 5678,
    },
    "trade": {
        "markets": 34567,
        "orders": 8901234,
        "updatedInLast24Hours": 123456,
        "uniqueCommodities": 289,
    },
    "timestamp": "2026-06-16T08:33:50.000Z",
}

ECONOMIES_PAYLOAD = {
    "primary": {
        "null": 100,
        "Agriculture": 200,
        "HighTech": 50,
    },
    "secondary": {
        "null": 300,
        "Industrial": 40,
    },
    "fleetCarriers": 1234,
    "timestamp": "2026-06-16T08:33:50.000Z",
}

STATION_TYPES_PAYLOAD = {
    "stationTypes": {
        "null": 10,
        "AsteroidBase": 20,
        "Bernal": 30,
        "Coriolis": 40,
        "CraterOutpost": 50,
        "CraterPort": 60,
        "Dodec": 70,
        "FleetCarrier": 80,
        "MegaShip": 90,
        "None": 5,
        "Ocellus": 100,
        "OnFootSettlement": 110,
        "Orbis": 120,
        "Outpost": 130,
        "PlanetaryConstructionDepot": 140,
        "SpaceConstructionDepot": 150,
        "StrongholdCarrier": 160,
        "SurfaceStation": 170,
    },
    "total": 1445,
    "timestamp": "2026-06-16T08:33:50.000Z",
}


@respx.mock
def test_get_version_returns_version():
    respx.get("https://api.ardent-insight.com/v2/version").mock(
        return_value=Response(200, json=VERSION_PAYLOAD)
    )

    client = ArdentClient()
    version = client.meta.get_version()

    assert version.version == "2.4.1"


@respx.mock
def test_get_stats_returns_stats():
    respx.get("https://api.ardent-insight.com/v2/stats").mock(
        return_value=Response(200, json=STATS_PAYLOAD)
    )

    client = ArdentClient()
    stats = client.meta.get_stats()

    assert stats.systems == 132456
    assert stats.points_of_interest == 987
    assert stats.stations.stations == 45678
    assert stats.stations.carriers == 1234
    assert stats.stations.updated_in_last_24_hours == 5678
    assert stats.trade.markets == 34567
    assert stats.trade.unique_commodities == 289


@respx.mock
def test_get_station_economies_returns_economies():
    respx.get("https://api.ardent-insight.com/v2/stats/stations/economies").mock(
        return_value=Response(200, json=ECONOMIES_PAYLOAD)
    )

    client = ArdentClient()
    economies = client.meta.get_station_economies()

    assert economies.primary.unspecified == 100
    assert economies.primary.agriculture == 200
    assert economies.primary.high_tech == 50
    assert economies.secondary.unspecified == 300
    assert economies.secondary.industrial == 40
    assert economies.fleet_carriers == 1234


@respx.mock
def test_get_station_economies_defaults_missing_fields_to_zero():
    respx.get("https://api.ardent-insight.com/v2/stats/stations/economies").mock(
        return_value=Response(200, json=ECONOMIES_PAYLOAD)
    )

    client = ArdentClient()
    economies = client.meta.get_station_economies()

    assert economies.primary.military == 0
    assert economies.secondary.tourism == 0


@respx.mock
def test_get_station_types_returns_station_types():
    respx.get("https://api.ardent-insight.com/v2/stats/stations/types").mock(
        return_value=Response(200, json=STATION_TYPES_PAYLOAD)
    )

    client = ArdentClient()
    station_types = client.meta.get_station_types()

    assert station_types.total == 1445
    assert station_types.station_types.unspecified == 10
    assert station_types.station_types.asteroid_base == 20
    assert station_types.station_types.none == 5
    assert station_types.station_types.surface_station == 170
