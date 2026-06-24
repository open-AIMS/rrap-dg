# Cyclones Module

The `cyclones` module generates cyclone mortality datasets for corals.

## Commands

### Command: generate

Generates a cyclone mortality datacube.

**Usage:**

```bash
uv run rrapdg cyclones generate RRAPDG_DATAPACKAGE_PATH RME_DATAPACKAGE_PATH OUTPUT_PATH
```

**Arguments:**

- `RRAPDG_DATAPACKAGE_PATH`: Path to the `rrap-dg` data package containing spatial and mortality data.
- `RME_DATAPACKAGE_PATH`: Path to the ReefMod Engine (RME) data package containing cyclone scenarios.
- `OUTPUT_PATH`: Directory to save the resulting `cyclone_mortality.nc` file.

**Options:**

- `--cluster-name TEXT`: Explicit name of the cluster geopackage. If not provided, the name is parsed and extracted automatically from the `RRAPDG_DATAPACKAGE_PATH` directory name.

## Implementation Details

The module utilizes a mortality regression model ported from an R script by **Dr. Vanessa Haller**. The implementation uses Julia to process data from:
- **Fabricius et al. (2008):** "Disturbance gradients on inshore and offshore coral reefs caused by a severe tropical cyclone."
- **ReefMod Engine (RME):** Data packages containing cyclone mortality scenarios.

Key processing steps:
- Maps cyclone windspeeds to mortality rates for functional groups.
- Accounts for depth-dependent mortality (e.g., branching vs. massive corals).
- Aligns and maps RME reefs with the target RRAP geopackage reefs using spatial intersection mapping and matching via **`GBRMPA_ID`** values (replaces the legacy mapping via `LABEL_ID`).

## Spatial Alignment and Edge Cases

### Unmatched Locations Handling
During spatial alignment, the generator checks which RME reefs overlap with the cluster sites:
1. It performs a spatial intersection check between the cluster site geometries (`rrap_gdf`) and the regional GBR reef polygons (`reefmod_gbr.gpkg`).
2. It maps the cluster sites to their parent RME reefs by matching their `UNIQUE_ID` identifiers.

Because the cluster geopackages contain high-resolution, downscaled site polygons, some detailed boundary or edge geometries might lie slightly outside the simplified regional borders of the macro RME reef polygons. 

To prevent these unmatched edge locations from causing indexing crashes (e.g. `BoundsError`), the generator defaults any unmatched site to **Category 0** (no cyclone / `0.0` windspeed). This guarantees that:
* The simulation finishes successfully for all cluster locations.
* Edge sites default to experiencing zero cyclone-induced mortality, which is logically correct.


