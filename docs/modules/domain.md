# Domain Module

The `domain` module provides tools for spatial processing of reef domains.

## Commands

### Command: cluster

Creates a new geopackage file with clustered locations using k-means optimization.

**Usage:**

```bash
uv run rrapdg domain cluster GPKG_PATH OUTPUT_PATH
```

**Arguments:**

- `GPKG_PATH`: Path to the input geopackage file.
- `OUTPUT_PATH`: Path to save the clustered geopackage.

### Command: prepare

Preprocesses the cluster geopackage by enforcing geographic coordinates (EPSG:4326), normalizing site ID column variations (such as `site_id` to `reef_siteid`), and mapping calibration groups (`CB_CALIB_GROUPS`) and carrying capacities (`k` values) from a canonical geopackage.

**Usage:**

```bash
uv run rrapdg domain prepare [OPTIONS]
```

**Options:**

- `--cluster-gpkg TEXT`: Path to the clustered geopackage. [Required]
- `--canonical-gpkg TEXT`: Path to the canonical geopackage. [Required]
- `--output-path TEXT`: Path to save the prepared geopackage. If not provided, it will overwrite the input cluster geopackage.

*Note: The deprecated command `update-cb-calib-groups` remains available as an alias for backward compatibility.*

## Implementation Details

- **Clustering**: Uses `BlackBoxOptim.jl` to find the optimal number of clusters, maximizing the Silhouette score and computing haversine distances.
- **Calibration Mapping Fallback Chain**: 
  1. **Site ID Suffix Matching**: Extracts GBRMPA ID from the `reef_siteid` column (e.g., `Lizard_14116B_Crest_1` -> `14116B`) and maps it to normalized GBRMPA IDs in the canonical geopackage.
  2. **UNIQUE_ID exact match**: Fallback match on `UNIQUE_ID`.
  3. **UNIQUE_ID prefix match**: Fallback match by stripping the last two digits of the `UNIQUE_ID` and matching prefix.
  4. **Defaults**: Fills any missing `CB_CALIB_GROUPS` or carrying capacity `k` values with `0`.
