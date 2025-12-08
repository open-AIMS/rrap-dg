# Integrated GBR Domain Generation

The `rrapdg` tool provides a streamlined workflow for generating GBR-wide ADRIA domains by pulling data directly from the RRAP Data Store or using local files.

## Command: `generate-domain-from-store`

This command downloads necessary datasets (Canonical, DHW, ReefMod Engine) using their unique handle IDs, formats them, and packages them into a ready-to-use ADRIA domain.

### Usage

```bash
rrapdg GBR generate-domain-from-store [OUTPUT_DIR] [OPTIONS]
```

### Arguments

*   `OUTPUT_DIR`: The directory where the generated domain and datapackage will be saved.

### Options

*   `--canonical-gpkg-handle TEXT`: Handle ID for the canonical geopackage.
*   `--canonical-gpkg-path PATH`: Local path to the canonical geopackage.
*   `--dhw-handle TEXT`: Handle ID for the DHW dataset.
*   `--dhw-path PATH`: Local path to the DHW dataset.
*   `--rme-handle TEXT`: Handle ID for the ReefMod Engine dataset.
*   `--rme-path PATH`: Local path to the ReefMod Engine dataset.
*   `--rcps TEXT`: Space-separated list of RCPs (e.g., "2.6 4.5 8.5"). Default: "2.6 4.5 7.0 8.5".
*   `--timeframe TEXT`: Space-separated start and end years (e.g., "2025 2099"). Default: "2025 2099".
*   `--config FILE`: Path to a TOML configuration file to specify arguments.

### Configuration File (TOML)

Using a configuration file is recommended for reproducibility.

**Example `config.toml`:**

```toml
[domain]
output_dir = "./my_gbr_domain"

[canonical]
handle = "10378.1/123456"
# path = "/local/path/to/canonical.gpkg"

[dhw]
handle = "10378.1/234567"

[rme]
path = "/local/path/to/rme_data"

[options]
rcps = "2.6 4.5 7.0 8.5"
timeframe = "2025 2060"
```

### Output Structure

The command generates a directory containing:

*   `datapackage.json`: Fully populated metadata file.
*   `spatial/`: Geopackage and coral cover NetCDF.
*   `DHWs/`: Formatted DHW NetCDF files.
*   `connectivity/`: Connectivity matrices.
*   `cyclones/`: (Placeholder if data not provided).
*   `waves/`: (Placeholder if data not provided).

**Note:** After generation, you must manually open `datapackage.json` and ensure the column mapping in the `spatial_data` resource description matches your geopackage (specifically `location_id_col`, `cluster_id_col`, `k_col`, and `area_col`).
