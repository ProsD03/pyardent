"""Read-only models for the API's metadata/statistics endpoints.

Unlike the resource models in the rest of `models/`, these are flat DTOs:
they don't carry a `_client` reference or expose further `get_*` traversal
methods, since the endpoints they map to (`/version`, `/stats`,
`/stats/stations/*`) are dead ends, not nodes in the API's resource graph.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel, to_pascal


# /version
class APIVersion(BaseModel):
    """Response of `GET /version`: the running Ardent API software version."""

    version: str


# /stats
class StationStats(BaseModel):
    """Station-related counters within `APIStats`."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stations: int
    carriers: int
    updated_in_last_24_hours: int


class TradeStats(BaseModel):
    """Trade-related counters within `APIStats`."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    markets: int
    orders: int
    updated_in_last_24_hours: int
    unique_commodities: int


class APIStats(BaseModel):
    """Response of `GET /stats`: database-wide counters, refreshed every 15 minutes."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    systems: int
    points_of_interest: int
    stations: StationStats
    trade: TradeStats
    timestamp: datetime


# /stats/stations/economies
class EconomyStats(BaseModel):
    """Station counts grouped by economy type, within `APIEconomies`.

    `unspecified` counts stations with no recorded economy (a SQL `NULL`,
    serialized by the API as the literal key `"null"`), as distinct from any
    of the named economy types below it.
    """

    model_config = ConfigDict(alias_generator=to_pascal, populate_by_name=True)

    unspecified: int = Field(default=0, alias="null")
    agriculture: int = 0
    colony: int = 0
    damaged: int = 0
    extraction: int = 0
    high_tech: int = 0
    industrial: int = 0
    military: int = 0
    prison: int = 0
    refinery: int = 0
    repair: int = 0
    rescue: int = 0
    service: int = 0
    terraforming: int = 0
    tourism: int = 0


class APIEconomies(BaseModel):
    """Response of `GET /stats/stations/economies`: station counts by primary/secondary economy.

    Excludes fleet carriers from the `primary`/`secondary` breakdowns; their
    count is reported separately via `fleet_carriers`.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    primary: EconomyStats
    secondary: EconomyStats
    fleet_carriers: int
    timestamp: datetime


# /stats/stations/types
class StationTypesStats(BaseModel):
    """Station counts grouped by station type, within `APIStations`.

    `unspecified` counts stations with no recorded type (a SQL `NULL`,
    serialized by the API as the literal key `"null"`). `none` is a distinct,
    much rarer bucket for the handful of records where the type was recorded
    as the literal string `"None"` rather than left unset.
    """

    model_config = ConfigDict(alias_generator=to_pascal, populate_by_name=True)
    unspecified: int = Field(alias="null")
    asteroid_base: int
    bernal: int
    coriolis: int
    crater_outpost: int
    crater_port: int
    dodec: int
    fleet_carrier: int
    mega_ship: int
    none: int
    ocellus: int
    on_foot_settlement: int
    orbis: int
    outpost: int
    planetary_construction_depot: int
    space_construction_depot: int
    stronghold_carrier: int
    surface_station: int


class APIStations(BaseModel):
    """Response of `GET /stats/stations/types`: station counts by station type."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    station_types: StationTypesStats
    total: int
    timestamp: datetime

