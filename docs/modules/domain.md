# Domain Module

The `domain` module provides tools for spatial processing of reef domains.

## Commands

### `cluster`

Creates a new geopackage file with clustered locations using k-means optimization.

**Usage:**

```bash
uv run rrap_dg domain cluster GPKG_PATH OUTPUT_PATH
```

**Arguments:**

- `GPKG_PATH`: Path to the input geopackage file.
- `OUTPUT_PATH`: Path to save the clustered geopackage.

## Implementation Details

- Uses `BlackBoxOptim.jl` to find the optimal number of clusters.
- Maximizes the Silhouette score to ensure distinct and meaningful clusters.
- Computes haversine distances between locations for accurate spatial clustering.
