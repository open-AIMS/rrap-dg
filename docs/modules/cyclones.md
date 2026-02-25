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

The module utilizes a mortality regression model ported from an R script by **Dr. Vanessa Haller**. The implementation uses Julia to process data from:
- **Fabricius et al. (2008):** "Disturbance gradients on inshore and offshore coral reefs caused by a severe tropical cyclone."
- **ReefMod Engine (RME):** Data packages containing cyclone mortality scenarios.

Key processing steps:
- Maps cyclone windspeeds to mortality rates for functional groups.
- Accounts for depth-dependent mortality (e.g., branching vs. massive corals).
