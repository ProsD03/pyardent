# pyardent

[![PyPI version](https://badge.fury.io/py/pyardent.svg)](https://badge.fury.io/py/pyardent)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![Type Check](https://github.com/ProsD03/pyardent/actions/workflows/type_check.yml/badge.svg)](https://github.com/ProsD03/pyardent/actions/workflows/type_check.yml)
[![Tests badge](https://raw.githubusercontent.com/ProsD03/pyardent/tests-badge-data/tests-badge.svg)](https://github.com/ProsD03/pyardent/actions/workflows/tests.yml)
[![Coverage badge](https://raw.githubusercontent.com/ProsD03/pyardent/python-coverage-comment-action-data/badge.svg)](https://github.com/ProsD03/pyardent/tree/python-coverage-comment-action-data)

A Python client for the [Ardent Insight](https://ardent-insight.com) API: trade and system data for Elite Dangerous.

Built on `httpx` and `pydantic`, fully type-hinted (ships a `py.typed` marker), with zero runtime dependencies beyond those two.

## Installation

```bash
pip install pyardent
```

Requires Python 3.12+.

## Quickstart

```python
from pyardent import ArdentClient

client = ArdentClient()

gold = client.commodity.get_by_name("gold")
print(gold)
#> commodity_name='gold' rare=False rare_station_id=None rare_max_count=None min_buy_price=3800 ...


sol = client.system.get_by_name("Sol")
stations = sol.get_stations()
lincoln = next(s for s in stations if s.station_name == "Abraham Lincoln")
print(lincoln)
#> system_address=10477373803 station_id=128016896 station_name='Abraham Lincoln' ...
```

## Why pyardent

Models aren't flat DTOs: they carry a reference back to the client, so you can traverse straight from one resource to another without manually threading IDs through further calls:

```python
gold = client.commodity.get_by_name("gold")

# Where can I sell gold for at least 50,000 credits, near Sol?
sol = client.system.get_by_name("Sol")
buyers = gold.get_nearby_importers(sol, min_price=50_000, max_distance=50)

for order in buyers:
    station = order.get_station()  # one more hop, still through the same client
    print(station.station_name, order.sell_price)
```

This graph-traversal pattern is consistent across the library: `System.get_stations()`, `Station.get_full_details()`, `Commodity.get_exporters()`, `CommodityMarket.get_station()`, and more.

## Error handling

Failed requests raise a typed exception instead of a bare `httpx.HTTPStatusError`:

```python
from pyardent import ArdentClient, SystemNotFoundError

client = ArdentClient()

try:
    client.system.get_by_name("Not A Real System")
except SystemNotFoundError:
    ...
```

All exceptions inherit from `PyArdentError`; more specific subclasses (`CommodityNotFoundError`, `ServiceNotFoundError`, `ResourceNotFoundError`) are raised where the API's error response is specific enough to tell them apart.

## Features

- Full pydantic models for every major resource: `System`, `Station`, `Commodity`, `CommodityMarket`
- Graph-traversal methods to move between related resources without re-fetching by hand
- A typed exception hierarchy instead of raw HTTP errors
- Custom `base_url` support, for pointing at a self-hosted or staging Ardent deployment
- Fully typed public API (`py.typed` included, so your type checker sees real types, not `Any`)

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync                                                        # install dependencies
uv run pytest                                                  # run tests
uv run pytest --cov=src/pyardent --cov-report=term-missing     # run tests with coverage
uv run mypy src                                                # type check
```

Contributions are welcome. Please make sure the commands above are clean before opening a pull request.

## AI Usage Disclosure

AI assistance (Claude Code) was used for parts of this project: documentation, the test suite, and general bug fixing.

The research into Ardent Insight's documented and undocumented API surface, the overall structure of the library, and most of the core implementation were written by hand.

## License

MIT. See [LICENSE.md](LICENSE.md) for details.
