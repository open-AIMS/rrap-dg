# Integrated GBR Domain Generation

The `rrapdg` tool provides a streamlined workflow for generating GBR-wide ADRIA domains by pulling data directly from the RRAP Data Store or using local files.

## Command: `generate-domain-from-store`

This command downloads necessary datasets (Canonical, DHW, ReefMod Engine) using their unique handle IDs or local paths, formats them, and packages them into a ready-to-use ADRIA domain.

### Usage

```bash
rrapdg GBR generate-domain-from-store [OUTPUT_PARENT_DIR] [DOMAIN_NAME] --config [CONFIG_FILE]
```

### Arguments

*   `OUTPUT_PARENT_DIR`: The parent directory where the generated domain folder will be created. The folder name will be auto-generated as `<DOMAIN_NAME>_<DATE>_v<VERSION>`.
*   `DOMAIN_NAME`: A short name for the domain (e.g., "GBR").

### Options

*   `--config`, `-c`: **(Required)** Path to a TOML configuration file defining the input datasets and parameters.

### Configuration File (TOML)

All domain parameters must be specified in a TOML configuration file.

**Example `config.toml`:**

```toml
[spatial]
location_id_col = "UNIQUE_ID"
cluster_id_col = "UNIQUE_ID"
k_col = "ReefMod_habitable_proportion"
area_col = "ReefMod_area_m2"
handle = "10378.1/123456" # Canonical GeoPackage handle (either handle or path)
# path = "/local/path/to/canonical.gpkg" # Canonical GeoPackage local path

[dhw]
handle = "10378.1/234567"
# path = "/local/path/to/dhw_data"

[rme]
handle = "10378.1/345678"
# path = "/local/path/to/rme_data"

[options]
rcps = "2.6 4.5 7.0 8.5"
timeframe = "2025 2060"
```

### Output Structure

The command generates a versioned directory (e.g., `GBR_2023-10-27_v080`) containing:

*   `datapackage.json`: Fully populated metadata file.
*   `spatial/`: Geopackage and coral cover NetCDF.
*   `DHWs/`: Formatted DHW NetCDF files.
*   `connectivity/`: Connectivity matrices.
*   `cyclones/`: (Placeholder if data not provided).
*   `waves/`: (Placeholder if data not provided).
