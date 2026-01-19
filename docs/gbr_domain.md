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

*   `rme_connectivity`: Extracts connectivity matrices from RME datafiles.
*   `standard_netcdf_dhw`: Formats standard DHW NetCDF files.
*   `rme_dhw`: Formats DHW data provided as CSVs in RME datasets.
*   `gbr_icc`: Initial Coral Cover from RME data using Julia.
*   `move_file_formatter`: Moves/Copies specific files from a source to the domain.

### Formatter Compatibility Matrix

Each formatter is designed to process specific datasets from the Data Store. The table below lists known compatible handles for each formatter.

| Formatter | Compatible Handles | Requirements / Notes |
| :--- | :--- | :--- |
| `rme_connectivity` | <ul><li> ReefMod Engine API v1.0.33 ([`102.100.100/705924`](https://hdl.handle.net/102.100.100/705924))</li><li> ReefMod Engine API ([`102.100.100/711073`](https://hdl.handle.net/102.100.100/711073))</li></ul> | ReefMod Engine Data files. Requires `con_csv` and `id` subdirectories. |
| `standard_netcdf_dhw`| <ul><li>DHW projections 2000-2100 (CMIP-6) v1 ([`102.100.100/483673`](https://hdl.handle.net/102.100.100/483673))</li><li>DHW projections 2000-2100 (CMIP-6) v2 ([`102.100.100/648083`](https://hdl.handle.net/102.100.100/648083))</li></ul> | Raw NetCDF Climate Data. Expects standard dimensions (`time`, `lat`, `lon`). |
| `rme_dhw` | <ul><li> ReefMod Engine API v1.0.33 ([`102.100.100/705924`](https://hdl.handle.net/102.100.100/705924))</li><li> ReefMod Engine API v1.0.43 ([`102.100.100/711073`](https://hdl.handle.net/102.100.100/711073))</li></ul> | ReefMod Engine Data files. Requires `dhw_csv` subdirectory. |
| `gbr_icc` | <ul><li> ReefMod Engine API v1.0.33 ([`102.100.100/705924`](https://hdl.handle.net/102.100.100/705924))</li><li> ReefMod Engine API v1.0.43 ([`102.100.100/711073`](https://hdl.handle.net/102.100.100/711073))</li></ul> | ReefMod Engine Data files. Requires full RME root structure. |
| `move_file_formatter`| <ul><li>N/A</li></ul> | Any dataset containing the file specified by the `filename_or_pattern` option. |

## DHW Output Structure and Model Mapping

The generated DHW NetCDF files (`dhwRCPxx.nc`) contain a `model` dimension which corresponds to an ensemble of climate models.

## Adding a New Formatter

If you need to process a new data source format, you can add a custom formatter by following these steps:

### 1. Define the Options Model

Create a Pydantic model for your formatter's specific options in `rrap_dg/format_gbr/models/options.py`. Inherit from `BaseFormatterOptions`.

```python
# rrap_dg/format_gbr/models/options.py
class MyCustomOptions(BaseFormatterOptions):
    input_pattern: str = Field("*.csv", description="Pattern to match input files.")
    # Add other required options here
```

### 2. Implement the Formatter Logic

Create a new class in `rrap_dg/format_gbr/formatters.py` that inherits from the `Formatter` abstract base class. Implement the `format` method.

```python
# rrap_dg/format_gbr/formatters.py
from .models import MyCustomOptions

class MyCustomFormatter(Formatter):
    description = "Formats my custom data source into a standard format."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        # Validate options using your Pydantic model
        opts = MyCustomOptions(**options)
        
        # Implement your logic here
        # source_path: The directory where the source data is located (downloaded or local)
        # output_path: The full path (including filename) where output should be written
        
        print(f"Processing data from {source_path} matching {opts.input_pattern}...")
        
        # Example: Copying a file (replace with your actual logic)
        # ...
```

### 3. Register the Formatter

Add your new class to the `FormatterRegistry` dictionary in `rrap_dg/format_gbr/formatters.py`.

```python
# rrap_dg/format_gbr/formatters.py

class FormatterRegistry:
    _formatters = {
        # ... existing formatters ...
        "my_custom_formatter": MyCustomFormatter,
    }
```

### 4. Use it in Configuration

You can now use your new formatter in the TOML configuration file:

```toml
[outputs.my_output]
type = "custom_type"
formatter = "my_custom_formatter"
source = "some_source_key"
filename = "my_output.csv" # or directory my_output
[outputs.my_output.options]
    input_pattern = "data_*.csv"
```
