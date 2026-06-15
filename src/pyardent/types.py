from enum import StrEnum, IntEnum


class StationServices(StrEnum):
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
    SMALL = 1
    MEDIUM = 2
    LARGE = 3