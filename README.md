# RRAP Data Generators

Provides a single command-line interface to generate data sets for use with [ADRIA](https://github.com/open-AIMS/ADRIA.jl) and the RRAP program.

[![PyPI - Version](https://img.shields.io/pypi/v/rrap-dg.svg)](https://pypi.org/project/rrap-dg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rrap-dg.svg)](https://pypi.org/project/rrap-dg)

---

## Documentation

Full documentation is available in the `docs/` directory.

*   **[Installation Guide](docs/installation.md)**: Setup instructions for Dev and Production.
*   **[CLI Reference](docs/cli.md)**: Command usage for DHW, ICC, Cyclones, and Clusters.
*   **[GBR Domain Generation](docs/gbr_domain.md)**: Guide for generating integrated GBR domains (`build-domain`).
*   **[Data Store](docs/data_store.md)**: Instructions for interacting with the RRAP M&DS Data Store and Data Package structures.

## Quick Start

### Installation

```console
# Create environment
mamba create -n rrap-dg python=3.11
mamba activate rrap-dg

# Install
pip install -e .
```

### Basic Usage

Run the help command to see available tools and trigger initial setup:

```bash
rrapdg --help
```

## Integrated GBR Domain Generation

To build a full domain from a configuration file:

```bash
rrapdg GBR build-domain ./output_dir ./config.toml
```

See the [GBR Domain Generation](docs/gbr_domain.md) docs for configuration details.

## License

`rrap-dg` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
