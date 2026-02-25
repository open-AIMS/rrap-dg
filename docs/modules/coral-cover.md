# Coral Cover Module

The `coral-cover` module handles the processing and downscaling of initial coral cover data.

## Commands

### `downscale-icc`

Creates a new netCDF with initial coral cover values downscaled to a specific cluster.

**Usage:**

```bash
uv run rrap_dg coral-cover downscale-icc RRAPDG_DPKG_PATH TARGET_CLUSTER OUTPUT_PATH
```

**Arguments:**

- `RRAPDG_DPKG_PATH`: Path to the source data package.
- `TARGET_CLUSTER`: Path to the target cluster's geopackage.
- `OUTPUT_PATH`: Path to save the resulting netCDF file.

## Implementation Details

- Aggregates RME scenario data to produce mean initial covers.
- Downscales data from large regional reefs to individual site locations.
- Converts absolute coral cover to values relative to carrying capacity ($k$).
