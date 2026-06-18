"""Tests for SystemModule.get_by_name.

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

import pytest
import respx
from httpx import Response

from pyardent import ArdentClient

SOL_PAYLOAD = {
    "systemAddress": 10477373803,
    "systemName": "Sol",
    "systemX": 0,
    "systemY": 0,
    "systemZ": 0,
    "systemSector": "a1b2c3d4e5f6a7b8",
    "updatedAt": "2026-06-16T08:33:50.000Z",
}

CVELORUM_PAYLOAD = [
  {
    "systemAddress": 84389401298,
    "systemName": "c Velorum",
    "systemX": 299.40625,
    "systemY": -0.3125,
    "systemZ": -7.625,
    "systemSector": "b54462392f48b156",
    "updatedAt": "2022-08-17T09:45:34.000Z",
    "ambiguous": True
  },
  {
    "systemAddress": 85261750986,
    "systemName": "C Velorum",
    "systemX": 844.5625,
    "systemY": -83.1875,
    "systemZ": -35.15625,
    "systemSector": "41087a2dd2d7d0b4",
    "updatedAt": "2022-11-26T00:18:27.000Z",
    "ambiguous": True
  }
]

# GET_BY_NAME

@respx.mock
def test_get_by_name_returns_system():
    respx.get("https://api.ardent-insight.com/v2/system/name/sol").mock(
        return_value=Response(200, json=SOL_PAYLOAD)
    )

    client = ArdentClient()
    system = client.system.get_by_name("Sol")

    assert system.system_name == "Sol"
    assert system.system_address == 10477373803


@respx.mock
def test_get_by_name_normalizes_case_and_whitespace():
    route = respx.get("https://api.ardent-insight.com/v2/system/name/sol").mock(
        return_value=Response(200, json=SOL_PAYLOAD)
    )

    client = ArdentClient()
    client.system.get_by_name("  SOL  ")

    assert route.called


def test_get_by_name_raises_on_empty_name():
    client = ArdentClient()

    with pytest.raises(ValueError):
        client.system.get_by_name("   ")



# SEARCH_BY_NAME

@respx.mock
def test_search_by_name_returns_all_systems():
    respx.get("https://api.ardent-insight.com/v2/search/system/name/c%20velorum").mock(
        return_value=Response(200, json=CVELORUM_PAYLOAD)
    )

    client = ArdentClient()
    systems = client.system.search_by_name("c velorum")
    assert len(systems) == 2
    assert systems[0].system_name == "c Velorum"

def test_search_by_name_raises_on_empty_name():
    client = ArdentClient()

    with pytest.raises(ValueError):
        client.system.search_by_name("   ")


# GET_BY_ADDRESS
@respx.mock
def test_get_by_address_returns_system():
    respx.get("https://api.ardent-insight.com/v2/system/address/10477373803").mock(
        return_value=Response(200, json=SOL_PAYLOAD)
    )
    client = ArdentClient()
    system = client.system.get_by_address("10477373803")

    assert system.system_address == 10477373803
    assert system.system_name == "Sol"


def test_get_by_address_raises_on_empty_address():
    client = ArdentClient()
    with pytest.raises(ValueError):
        client.system.get_by_address("")

def test_get_by_address_raises_on_negative_address():
    client = ArdentClient()
    with pytest.raises(ValueError):
        client.system.get_by_address(-1)