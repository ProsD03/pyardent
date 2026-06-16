"""Shared enums used across modules and models for query parameters."""

from enum import StrEnum, IntEnum


class StationServices(StrEnum):
    """Station service types accepted by `System.get_nearest_service`.

    Values match the `{service}` path segment of the API's
    `/system/.../nearest/{service}` endpoint.
    """

    INTERSTELLAR_FACTORS = "interstellar-factors"
    MATERIAL_TRADER = "material-trader"
    TECHNOLOGY_BROKER = "technology-broker"
    BLACK_MARKET = "black-market"
    UNIVERSAL_CARTOGRAPHICS = "universal-cartographics"
    REFUEL = "refuel"
    REPAIR = "repair"
    SHIPYARD = "shipyard"
    OUTFITTING = "outfitting"
    SEARCH_AND_RESCUE = "search-and-rescue"

class LandingPad(IntEnum):
    """Landing pad size, as used by `maxLandingPadSize`/`minLandingPadSize` query params and fields."""

    SMALL = 1
    MEDIUM = 2
    LARGE = 3