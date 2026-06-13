from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel, to_pascal


# /version
class APIVersion(BaseModel):
    version: str


# /stats
class StationStats(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stations: int
    carriers: int
    updated_in_last_24_hours: int


class TradeStats(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    markets: int
    orders: int
    updated_in_last_24_hours: int
    unique_commodities: int


class APIStats(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    systems: int
    points_of_interest: int
    stations: StationStats
    trade: TradeStats
    timestamp: datetime


# /stats/stations/economies
class EconomyStats(BaseModel):
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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    primary: EconomyStats
    secondary: EconomyStats
    fleet_carriers: int
    timestamp: datetime


# /stats/stations/types
class StationTypesStats(BaseModel):
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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    station_types: StationTypesStats
    total: int
    timestamp: datetime

