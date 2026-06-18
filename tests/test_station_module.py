from httpx import Response

from pyardent import ArdentClient
import respx
import pytest

OBSIDIAN_ORBITAL = {
  "marketId": 128672445,
  "stationName": "Obsidian Orbital",
  "distanceToArrival": 632.034764,
  "stationType": "Ocellus",
  "allegiance": None,
  "government": "Patronage",
  "controllingFaction": "Anti Xeno Initiative",
  "primaryEconomy": "HighTech",
  "secondaryEconomy": None,
  "shipyard": 1,
  "outfitting": 1,
  "blackMarket": 0,
  "contacts": 1,
  "crewLounge": 1,
  "interstellarFactors": 0,
  "materialTrader": 0,
  "missions": 1,
  "refuel": 1,
  "repair": 1,
  "restock": 0,
  "searchAndRescue": 1,
  "technologyBroker": 0,
  "tuning": 1,
  "universalCartographics": 1,
  "systemAddress": 8216113749,
  "systemName": "Maia",
  "systemX": -81.78125,
  "systemY": -149.4375,
  "systemZ": -343.375,
  "bodyId": 11326,
  "bodyName": "Maia A 2 a",
  "latitude": None,
  "longitude": None,
  "maxLandingPadSize": 3,
  "updatedAt": "2026-06-18T00:03:37.482Z"
}

@respx.mock
def test_get_by_id():
    respx.get("https://api.ardent-insight.com/v2/market/128672445").mock(return_value=Response(200, json=OBSIDIAN_ORBITAL))

    client = ArdentClient()
    station = client.station.get_by_id(128672445)

    assert station.station_name == "Obsidian Orbital"
    assert station.station_id == 128672445

def test_get_by_id_raises_empty_id():
    client = ArdentClient()

    with pytest.raises(ValueError):
        client.station.get_by_id("")

def test_get_by_id_raises_negative_id():
    client = ArdentClient()

    with pytest.raises(ValueError):
        client.station.get_by_id(-1)

@respx.mock
def test_search_by_name():
    respx.get("https://api.ardent-insight.com/v2/search/station/name/obsidian%20orbital").mock(return_value=Response(200, json=[OBSIDIAN_ORBITAL]))

    client = ArdentClient()
    stations = client.station.search_by_name("obsidian orbital")

    assert len(stations) == 1
    assert stations[0].station_name == "Obsidian Orbital"

def test_search_by_name_raises_empty_name():
    client = ArdentClient()

    with pytest.raises(ValueError):
        client.station.search_by_name("   ")

