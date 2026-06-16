"""Entry point for the API's system resource (`/system/...`, `/search/system/...`)."""

import logging
from urllib.parse import unquote, quote

import httpx

from ..models import System

logger = logging.getLogger("pyardent.modules.system")

class SystemModule:
    """Attached as `ArdentClient.system`. Looks up systems to start traversing from."""

    _client: httpx.Client

    def __init__(self, client: httpx.Client):
        self._client = client

    def get_by_name(self, name: str) -> System:
        """Fetch one system by its exact name.

        Some system names aren't unique; if so, the result's
        `disambiguation` field is populated with the other matches.

        Args:
            name: The system name. Case-insensitive.

        Returns:
            The matching `System`.

        Raises:
            ValueError: If `name` is empty after normalization.
            SystemNotFoundError: If no system matches.
        """
        normalized_name = unquote(name).lower().strip()
        if not normalized_name:
            raise ValueError("name cannot be empty")
        url_encoded_name = quote(normalized_name, safe='')

        logger.debug(f"GET /system/name/{url_encoded_name}")
        response = self._client.get(f"/system/name/{url_encoded_name}")
        return System.from_json(self._client, payload=response.json())

    def search_by_name(self, name: str) -> list[System]:
        """Search for systems whose name starts with the given text.

        This is a prefix search (suitable for autocomplete), not an exact
        match — unlike `get_by_name`, which returns a single exact result.

        Args:
            name: The name prefix to search for. Case-insensitive.

        Returns:
            Up to 25 matching systems.

        Raises:
            ValueError: If `name` is empty after normalization.
        """
        normalized_name = unquote(name).lower().strip()
        if not normalized_name:
            raise ValueError("name cannot be empty")
        url_encoded_name = quote(normalized_name, safe='')

        logger.debug(f"GET /search/system/name/{url_encoded_name}")
        response = self._client.get(f"/search/system/name/{url_encoded_name}")
        systems = response.json()
        logger.debug(f"Parsing {len(systems)} matching systems")
        return [System.from_json(self._client, system) for system in systems]

    def get_by_address(self, address: str | int) -> System:
        """Fetch one system by its unique system address.

        Unlike a system name, an address is always unambiguous — useful
        when disambiguating a name that has multiple matches.

        Args:
            address: The system address.

        Returns:
            The matching `System`.

        Raises:
            ValueError: If `address` is empty, or negative when given as an int.
            SystemNotFoundError: If no system matches.
        """
        normalized_address = str(address).strip()
        if not normalized_address:
            raise ValueError("address cannot be empty")
        if isinstance(address, int) and address < 0:
            raise ValueError(f"address cannot be negative. received: {address}")
        url_encoded_address = quote(normalized_address, safe='')

        logger.debug(f"GET /system/address/{url_encoded_address}")
        response = self._client.get(f"/system/address/{url_encoded_address}")
        return System.from_json(self._client, payload=response.json())
