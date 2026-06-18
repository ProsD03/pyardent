from pyardent import ArdentClient
from pyardent.models.station import Station

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
OBSIDIAN_ORBITAL_NO_SHIPYARD = {
  "marketId": 128672445,
  "stationName": "Obsidian Orbital",
  "distanceToArrival": 632.034764,
  "stationType": "Ocellus",
  "allegiance": None,
  "government": "Patronage",
  "controllingFaction": "Anti Xeno Initiative",
  "primaryEconomy": "HighTech",
  "secondaryEconomy": None,
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

def test_station_data_explode():
    client = ArdentClient()
    station = Station.from_json(client._client, OBSIDIAN_ORBITAL)

    assert station.station_name == "Obsidian Orbital"
    assert station.services is not None
    assert station.services.shipyard is True

def test_station_data_explode_missing_service():
    client = ArdentClient()
    station = Station.from_json(client._client, OBSIDIAN_ORBITAL_NO_SHIPYARD)

    assert station.station_name == "Obsidian Orbital"
    assert station.services is not None
    assert station.services.shipyard is None

