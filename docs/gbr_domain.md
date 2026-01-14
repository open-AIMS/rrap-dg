# Integrated GBR Domain Generation

This command generates a complete GBR-wide ADRIA Domain by consolidating data from various sources (RME, Data Store, local files) using a flexible TOML configuration.

## Command: `build-domain`

```console
(rrap-dg) $ rrapdg GBR build-domain [OUTPUT_PARENT_DIR] [CONFIG_FILE]
```

*   `OUTPUT_PARENT_DIR`: The parent directory where the generated domain folder will be created.
*   `CONFIG_FILE`: Path to the TOML configuration file.

The domain will be saved in a new directory named `<DOMAIN_NAME>_YYYY-MM-DD_v<VERSION>` within the `OUTPUT_PARENT_DIR`.

## Configuration File (TOML) Example

The configuration is split into `sources` (where data comes from) and `outputs` (what files are created).

The following example is for generating a GBR wide domain using connectivity, initial coral
cover from ReefMod Engine and a seperate DHWs source.

```toml
domain_name = "GBR_Domain"

[sources]
    [sources.spatial_base]
    handle = "102.100.100/711118"

    [sources.dhw_data]
    handle = "102.100.100/705397"

    [sources.rme_data]
    handle = "102.100.100/705924"

[outputs.connectivity]
type = "connectivity"
format = "csv"
formatter = "rme_connectivity"
source = "rme_data"
filename = "connectivity" # Output directory for CSVs
[outputs.connectivity.options]
    spatial_source = "spatial_base"


# Generate Degree Heating Weeks (DHWs)
[outputs.dhw]
type = "dhw"
formatter = "standard_netcdf_dhw"
source = "dhw_data"
filename = "DHWs" # Output directory for NetCDFs
[outputs.dhw.options]
    rcps = "2.6 4.5 7.0 8.5"
    timeframe = "2025 2099"


# Generate Initial Coral Cover
[outputs.coral_cover]
type = "initial_coral_cover"
format = "netcdf"
formatter = "gbr_icc"
source = "rme_data"
filename = "spatial/coral_cover.nc"
[outputs.coral_cover.options]
    canonical_source = "spatial_base"


[outputs.spatial_data]
type = "spatial_data"
format = "geopackage"
formatter = "move_file_formatter"
source = "spatial_base"
filename = "spatial/canonical.gpkg"
[outputs.spatial_data.options]    
    filename_or_pattern = "rrap_canonical*.gpkg"

```

## Available Formatters

*   `rme_connectivity`: Extracts connectivity matrices from RME datasets.
*   `standard_netcdf_dhw`: Formats standard DHW NetCDF files.
*   `rme_dhw`: Formats DHW data provided as CSVs in RME datasets.
*   `gbr_icc`: Downscales Initial Coral Cover from RME data using Julia.
*   `move_file_formatter`: Moves/Copies specific files from a source to the domain.

## DHW Output Structure and Model Mapping

The generated DHW NetCDF files (`dhwRCPxx.nc`) contain a `model` dimension which corresponds to an ensemble of climate models.