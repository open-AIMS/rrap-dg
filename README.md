# RRAP Data Generator

[![PyPI - Version](https://img.shields.io/pypi/v/rrap-dg.svg)](https://pypi.org/project/rrap-dg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rrap-dg.svg)](https://pypi.org/project/rrap-dg)

The **RRAP Data Generator** (`rrap_dg`) is a command-line tool designed to generate and format data for the Reef Restoration and Adaptation Program (RRAP). It provides a unified interface to process environmental data, generate mortality scenarios, and package datasets for use in modeling frameworks like ADRIA.

## Documentation

Full documentation is available in the `docs/` directory or can be served locally using:

```bash
uv run mkdocs serve
```

Key documentation sections:
- [Getting Started](docs/getting-started.md) - Installation and environment setup.
- [CLI Usage](docs/cli-usage.md) - Command pattern and module overview.
- [Data Package Structure](docs/modules/data-packages.md) - Standard directory layout for source data.
- [Metadata & Packaging Logic](docs/development.md) - Details on how `datapackage.json` is generated.

## Installation

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/open-AIMS/rrap-dg
cd rrap-dg

# Install dependencies and create a virtual environment
$ uv sync

# Run the help command
$ uv run rrap_dg --help
```

## Available Modules

The tool is organized into several specialized modules:

- `dhw`: Degree Heating Week projections.
- `cyclones`: Cyclone mortality modeling.
- `domain`: Spatial clustering of reef sites.
- `coral-cover`: Processing of initial coral cover.
- `data-store`: Interaction with the RRAP M&DS Data Store.
- `template`: Automated building of domain data packages.
- `format`: Converters for various RME and CMIP6 data formats.

To see available commands for a module:
```bash
uv run rrap_dg [MODULE] --help
```

## License

`rrap-dg` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
