# Domain Build Guide

This guide provides a step-by-step walkthrough of building a clustered ADRIA-compatible domain package using the `rrap-dg` command-line tools.

---

## Workflow Overview

The domain generation process consists of three main stages:

```mermaid
graph TD
    A["1. (Optional Geopackage Creation) & Calibration Group Insertion"]
    
    A --> B["2a. Downscale ICC"]
    A --> C["2b. Generate DHW Projections"]
    A --> D["2c. Generate Cyclone Mortality"]
    
    B --> E["3. Compile Domain Package"]
    C --> E
    D --> E
```

---

## Step 1: (Optional Geopackage Creation) & Calibration Group Insertion

Define the clustered spatial boundary (see the [Available Clusters & Geopackages](modules/cluster-resources.md#available-clusters-geopackages) section in the [Cluster Resources](modules/cluster-resources.md) guide) and map calibration groups (`CB_CALIB_GROUPS`) and carrying capacities (`k` values) from a canonical geopackage.

1. **(Optional) Run Clustering:**
   If you do not have a pre-clustered geopackage, cluster the canonical geopackage locations using k-means:
   ```bash
   uv run rrapdg domain cluster <CANONICAL_GPKG_PATH> <CLUSTER_GPKG_PATH>
   ```
2. **Apply Calibration Mapping Fallbacks:**
   Map carrying capacity and calibration groups onto the cluster geopackage:
   ```bash
   uv run rrapdg domain update-cb-calib-groups \
     --cluster-gpkg <CLUSTER_GPKG_PATH> \
     --canonical-gpkg <CANONICAL_GPKG_PATH>
   ```

---

## Step 2a: Downscale Initial Coral Cover (ICC)

Downscale the Initial Coral Cover data from the source data package to match your target cluster's locations and carrying capacity ($k$):

```bash
uv run rrapdg coral-cover downscale-icc <SOURCE_DPKG_PATH> <CLUSTER_GPKG_PATH> <FORMATTED_DIR>/coral_cover.nc
```

---

## Step 2b: Generate Cluster-Specific DHW Projections

Generate stochastic Degree Heating Week projections for the specific cluster name, utilizing satellite NOAA baselines, MIROC5 CMIP6 trends, and local RECOM heatwave spatial patterns (see the [Available RECOM Datasets](modules/cluster-resources.md#available-recom-datasets) section in the [Cluster Resources](modules/cluster-resources.md) guide).

```bash
uv run rrapdg dhw generate \
  --gpkg-path <CLUSTER_GPKG_PATH> \
  --recom-dir <RECOM_DIR_PATH> \
  <CLUSTER_NAME> <SHARED_INPUT_DIR> <FORMATTED_DIR>/DHWs
```

*Note: `<SHARED_INPUT_DIR>` must contain the `NOAA/`, `MIROC5/`, and `spatial/` subdirectories.*

---

## Step 2c: Generate Cyclone Mortality

Generate a cluster-specific cyclone mortality NetCDF datacube using the RME cyclone scenarios and target cluster spatial geometries:

```bash
uv run rrapdg cyclones generate \
  --cluster-name <CLUSTER_NAME> \
  <FORMATTED_DIR> <RME_ROOT_DIR> <FORMATTED_DIR>/cyclones
```

---

!!! tip "Provenance Best Practice"
    Before compiling the final domain package, it is highly recommended to upload your newly generated and formatted datasets (e.g., DHWs, cyclones, initial coral cover) to the **RRAP M&DS Data Store**.

    When building the domain, specify the **Data Store Handle IDs** as the `source` values in your `config.toml`. The packaging tool will automatically query and download the rich metadata from the Data Store, populating the final `datapackage.json` with accurate provenance and lineage tracking instead of raw local paths.

## Step 3: Compile and Finalize the Domain Package

Assemble the processed and generated components into the final ADRIA domain package structure (matching the standard [Standard Data Package Layout](modules/cluster-resources.md#standard-data-package-layout)), writing the standard `datapackage.json` metadata containing full dataset provenance.

The domain is compiled using a TOML configuration file defining the sources for all required data layers.

### 1. Create a `config.toml` File
Create a configuration file mapping out your local filepaths or RRAP M&DS Data Store handle IDs:

```toml
domain_name = "Cairns_Test"

[spatial]
source = "/path/to/spatial/Cairns.gpkg"

[dhw]
source = "/path/to/formatted/DHWs"

[connectivity]
source = "/path/to/user/connectivity"  # Must align with the canonical geopackage

[icc]
source = "/path/to/formatted/coral_cover.nc"

[cyclones]
source = "/path/to/formatted/cyclones"
```

### 2. Run the Build Command
Pass the configuration file path and the base output directory to the template builder:

```bash
uv run rrapdg template build <CONFIG_PATH> <OUTPUT_PATH>
```

---

## Guide Notes

### Parameter Meanings:
* **`domain_name` (in config):** The target name for your domain. The builder will automatically append the date and version tag (e.g., `Cairns_Test_2026-06-24_v080`) to form the final directory name and rename the internal geopackage to match it.
* **`<OUTPUT_PATH>`:** The parent directory where the final domain package directory will be created. The domain will be generated at `<OUTPUT_PATH>/<domain_name>_<date>_v<version>/`.
* **`source` parameters:** Each `source` field in the TOML configuration can be set to either a **local directory/filepath** or an **M&DS Data Store Handle ID** (e.g., `102.100.100/XXXXXX`).
