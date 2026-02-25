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

### `bin-edge-icc`

Creates a set of netCDF files in an output directory based on bin edges defined in a TOML file.

**Usage:**

```bash
uv run rrap_dg coral-cover bin-edge-icc RRAPDG_DPKG_PATH TARGET_GPKG OUTPUT_DIR TOML_FILE
```

**Arguments:**

- `RRAPDG_DPKG_PATH`: Path to the source `rrap-dg` data package.
- `TARGET_GPKG`: Path to the target cluster's geopackage.
- `OUTPUT_DIR`: Directory where the netCDF files will be saved.
- `TOML_FILE`: Path to a TOML file defining the bin edges.

#### TOML File Format

The TOML file defines matrices for each bin edge. Each matrix has 6 rows (representing functional groups) and columns for each size class.

**Example `bin_edges.toml`:**

```toml
bin_edge_1 = [
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [5.0, 7.5, 10.0, 20.0, 40.0, 100.0, 150.0],
    [5.0, 7.5, 10.0, 20.0, 35.0, 50.0, 100.0],
    [5.0, 7.5, 10.0, 15.0, 20.0, 40.0, 50.0],
    [5.0, 7.5, 10.0, 20.0, 40.0, 50.0, 100.0],
    [5.0, 7.5, 10.0, 20.0, 40.0, 50.0, 100.0]
]
```

## Implementation Details

- **Source Support:** Compatible with ReefMod or RME v1.0.x datasets or the `rrap-dg` data package.
- **Carrying Capacity:** Converts absolute coral cover to values relative to carrying capacity ($k$).
- **Spatial Alignment:** Automatically aligns RME reef identifiers with the target geopackage's site locations.
