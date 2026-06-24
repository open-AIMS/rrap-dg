# CLI Usage

The RRAP Data Generator provides a unified CLI entry point.

## General Command Structure

All commands follow this pattern:

```bash
uv run rrapdg [MODULE] [COMMAND] [OPTIONS]
```

To see the available modules:

```bash
uv run rrapdg --help
```

## Available Modules

| Module | Description |
| :--- | :--- |
| `dhw` | Generate Degree Heating Week datasets. |
| `cyclones` | Generate Cyclones mortality datasets. |
| `domain` | Cluster locations in a geopackage. |
| `coral-cover` | Downscale initial coral cover values. |
| `data-store` | Interact with the RRAP M&DS Data Store. |
| `template` | Build and manage ADRIA Domain packages. |
| `format` | Reformat RME and CMIP6 datasets. |

For detailed information on a specific module, use:

```bash
uv run rrapdg [MODULE] --help
```
