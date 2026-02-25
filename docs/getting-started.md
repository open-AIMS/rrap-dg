# Getting Started

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

To install the project and its dependencies:

```bash
uv sync
```

## Environment Configuration

The application uses Pydantic Settings for configuration. You can create a `.env` file in the project root to override default values.

### Example `.env` File

```bash
# Data Store Connection
PROVENA_DOMAIN=mds.gbrrestoration.org
PROVENA_REALM_NAME=rrap
PROVENA_CLIENT_ID=automated-access

# Cache Management
DATA_STORE_CACHE_DIR=~/.cache/rrap-dg
```

### Available Settings

| Setting | Description | Default |
| :--- | :--- | :--- |
| `PROVENA_DOMAIN` | The Provana Data Store deployment domain. | `mds.gbrrestoration.org` |
| `PROVENA_REALM_NAME` | The Keycloak authentication realm. | `rrap` |
| `PROVENA_CLIENT_ID` | The Keycloak client ID for automated access. | `automated-access` |
| `DATA_STORE_CACHE_DIR` | Local directory for caching datasets. | `~/.cache/rrap-dg` |

## Documentation

To serve the documentation locally:

```bash
uv run mkdocs serve
```

To build the documentation:

```bash
uv run mkdocs build
```
