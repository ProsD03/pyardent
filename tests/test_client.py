"""Tests for ArdentClient construction: base_url handling and module wiring.

respx intercepts HTTP requests at the transport level, so ArdentClient's
real httpx.Client never touches the network during these tests - we control
exactly what the "API" returns.
"""

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


def test_default_base_url_is_used_when_omitted():
    client = ArdentClient()

    assert client._base_url == ArdentClient.DEFAULT_BASE_URL == "https://api.ardent-insight.com/v2"
    assert str(client._client.base_url) == "https://api.ardent-insight.com/v2/"


@respx.mock
def test_default_base_url_is_used_for_requests():
    respx.get("https://api.ardent-insight.com/v2/system/name/sol").mock(
        return_value=Response(200, json=SOL_PAYLOAD)
    )

    client = ArdentClient()
    system = client.system.get_by_name("Sol")

    assert system.system_name == "Sol"


def test_custom_base_url_overrides_default():
    client = ArdentClient(base_url="https://staging.example.com/v3")

    assert client._base_url == "https://staging.example.com/v3"
    assert str(client._client.base_url) == "https://staging.example.com/v3/"


@respx.mock
def test_custom_base_url_is_used_for_requests():
    respx.get("https://staging.example.com/v3/system/name/sol").mock(
        return_value=Response(200, json=SOL_PAYLOAD)
    )

    client = ArdentClient(base_url="https://staging.example.com/v3")
    system = client.system.get_by_name("Sol")

    assert system.system_name == "Sol"


def test_modules_share_the_client_httpx_client():
    client = ArdentClient()

    assert client.meta._client is client._client
    assert client.commodity._client is client._client
    assert client.system._client is client._client
    assert client.station._client is client._client
