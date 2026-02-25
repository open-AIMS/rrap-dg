# Cyclones Module

The `cyclones` module generates cyclone mortality datasets for corals.

## Commands

### `generate`

Generates a cyclone mortality datacube.

**Usage:**

```bash
uv run rrap_dg cyclones generate RRAPDG_DATAPACKAGE_PATH RME_DATAPACKAGE_PATH OUTPUT_PATH
```

**Arguments:**

- `RRAPDG_DATAPACKAGE_PATH`: Path to the `rrap-dg` data package containing spatial and mortality data.
- `RME_DATAPACKAGE_PATH`: Path to the ReefMod Engine (RME) data package containing cyclone scenarios.
- `OUTPUT_PATH`: Directory to save the resulting `cyclone_mortality.nc` file.

## Implementation Details

This module utilizes Julia for data processing:
- It fits regression models to coral cover mortality data.
- It maps cyclone windspeeds to mortality rates for different coral groups (branching, massive).
- It accounts for depth-dependent mortality for branching corals.
