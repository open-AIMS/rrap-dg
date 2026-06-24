# DHW Module

The `dhw` module is responsible for generating projected Degree Heating Week (DHW) datasets for specific reef clusters.

## Commands

### Command: generate

Produces Degree Heating Week projections for a given cluster.

*If you have already downloaded the RECOM and geospatial files seperately from the standard
datapackage layout you can pass these filepaths directly instead of specifying a cluster
name.*

**Usage:**

```bash
uv run rrapdg dhw generate [OPTIONS] CLUSTER_NAME INPUT_LOC OUTPUT_LOC
```

**Arguments:**

- `CLUSTER_NAME`: Name of the geopackage file (e.g., the reef cluster name).
- `INPUT_LOC`: Directory containing the source datasets (NOAA historical, MIROC5 projections, RECOM patterns).
- `OUTPUT_LOC`: Directory where the generated netCDF files will be saved.

**Options:**

- `--n-sims INTEGER`: Number of simulation members to generate (default: 50).
- `--rcps TEXT`: Space-separated list of RCP scenarios (default: "2.6 4.5 6.0 8.5").
- `--gen-year TEXT`: Timeframe for projections "START END" (default: "2025 2100").
- `--gpkg-path TEXT`: Direct path to the cluster geopackage file.
- `--recom-dir TEXT`: Direct path to the directory containing RECOM files.

## Implementation Details

The `dhw` module generates projections using a combination of:
- **NOAA Coral Reef Watch (CRW version 3.1)** satellite data.
- **MIROC5 RCP projections** (2021 - 2099).
- **RECOM** spatial multi-marine heat wave patterns.

This work was ported to Python from original MATLAB code developed by **Dr. Veronique Lago** and modified by **Chinenye Ani**.

The generation process involves:
1. Extracting target areas from historical NOAA data.
2. Detrending historical data using Gaussian fits.
3. Stochastically generating yearly projections based on Generalized Extreme Value (GEV) distributions.
4. Applying spatial adjustments based on RECOM heatwave patterns.
