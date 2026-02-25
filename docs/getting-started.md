# Getting Started

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

To install the project and its dependencies:

```bash
uv sync
```

## Environment Setup

If you intend to use the `data-store` module to download data from the RRAP M&DS Data Store, you may need to configure your environment.

The application uses Pydantic Settings to manage configuration. You can create a `.env` file in the root directory:

```env
PROVENA_DOMAIN=mds.gbrrestoration.org
PROVENA_CLIENT_ID=automated-access
DATA_STORE_CACHE_DIR=~/.cache/rrap-dg
```

## Documentation

To serve the documentation locally:

```bash
uv run mkdocs serve
```

To build the documentation:

```bash
uv run mkdocs build
```
