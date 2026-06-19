import pytest
import respx
from httpx import Response
from pyardent import ArdentClient

COMMODITIES = [
  {
    "commodityName": "advancedcatalysers",
    "minBuyPrice": 219,
    "maxBuyPrice": 3035,
    "avgBuyPrice": 2446,
    "totalStock": 234250516,
    "minSellPrice": 218,
    "maxSellPrice": 3756,
    "avgSellPrice": 3205,
    "totalDemand": 4628323413,
    "timestamp": "2025-05-08T09:15:06.476Z"
  },
  {
    "commodityName": "advancedmedicines",
    "minBuyPrice": 91,
    "maxBuyPrice": 3471,
    "avgBuyPrice": 1049,
    "totalStock": 11709556,
    "minSellPrice": 86,
    "maxSellPrice": 4805,
    "avgSellPrice": 1717,
    "totalDemand": 3980167772,
    "timestamp": "2025-05-08T09:15:11.136Z"
  },
]

GOLD = {
  "commodityName": "gold",
  "minBuyPrice": 3981,
  "maxBuyPrice": 60290,
  "avgBuyPrice": 44630,
  "totalStock": 126303255,
  "minSellPrice": 3980,
  "maxSellPrice": 67620,
  "avgSellPrice": 49027,
  "totalDemand": 3408604950,
  "timestamp": "2025-05-08T09:20:08.043Z"
}

OPAL = {
  "commodityName": "opal",
  "minBuyPrice": None,
  "maxBuyPrice": None,
  "avgBuyPrice": None,
  "totalStock": 0,
  "minSellPrice": 3415,
  "maxSellPrice": 769355,
  "avgSellPrice": 143465,
  "totalDemand": 18768892,
  "timestamp": "2025-05-08T09:23:56.902Z"
}

@respx.mock
def test_get_all():
    respx.get("https://api.ardent-insight.com/v2/commodities").mock(return_value=Response(200, json=COMMODITIES))

    client = ArdentClient()
    commodities = client.commodity.get_all()
    assert len(commodities) == 2
    assert commodities[0].commodity_name == "advancedcatalysers"

@respx.mock
def test_get_by_name():
    respx.get("https://api.ardent-insight.com/v2/commodity/name/gold").mock(return_value=Response(200, json=GOLD))

    client = ArdentClient()
    commodity = client.commodity.get_by_name("gold")
    assert commodity.commodity_name == "gold"

@respx.mock
def test_get_by_name_alias():
    respx.get("https://api.ardent-insight.com/v2/commodity/name/opal").mock(return_value=Response(200, json=OPAL))

    client = ArdentClient()
    commodity = client.commodity.get_by_name("void opal")
    assert commodity.commodity_name == "opal"

def test_get_by_name_raises_empty_name():
    client = ArdentClient()
    with pytest.raises(ValueError):
        client.commodity.get_by_name("")