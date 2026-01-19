# Data Store Interaction

The `rrapdg` tool includes commands to interact with the RRAP M&DS Data Store, powered by Provena.

## Command Group: `data-store`

Use these commands to fetch datasets.

### `download`

Download a dataset by its handle ID to a specified directory.

```bash
rrapdg data-store download [HANDLE_ID] [OUTPUT_DIRECTORY]
```

*   `HANDLE_ID`: The unique identifier for the dataset (e.g., `10378.1/123456`).
*   `OUTPUT_DIRECTORY`: The local folder where files will be saved.

### `download-w-cache`

Download a dataset by its handle ID to the system cache (default `~/.cache/rrap-dg`). If the dataset is already cached, it will not be re-downloaded unless forced.

```bash
rrapdg data-store download-w-cache [HANDLE_ID] [--force]
```

*   `HANDLE_ID`: The unique identifier for the dataset.
*   `--force`: (Optional) If set, clears the existing cache for this dataset and re-downloads it.

## rrap-dg Data Packages

The rrap-dg Data Packages are used as inputs by DHW and Cyclone Mortality data generators.

### Required Folders

*   **DHW Generation**: Requires `MIROC5`, `NOAA`, `RECOM`, and `spatial`.
*   **Cyclone Mortality**: Requires `cyclone_mortality` (or `cyclones` in some contexts).

### Naming Convention

The data package should be named with the following convention:

`[cluster name]_rrapdg_[YYYY-MM-DD]`

### Example Structure

An example for a hypothetical Moore dataset:

```bash
Moore_rrapdg_2023-01-24
│   datapackage.json
│   README.md
│
├───MIROC5
│       GBR_maxDHW_MIROC5_rcp26_2021_2099.csv
│       GBR_maxDHW_MIROC5_rcp45_2021_2099.csv
│       GBR_maxDHW_MIROC5_rcp60_2021_2099.csv
│       GBR_maxDHW_MIROC5_rcp85_2021_2099.csv
│
├───NOAA
│       GBR_dhw_hist_noaa.nc
│
├───RECOM
│       Moore_2015_585_dhw_exp.nc
│       Moore_2016_586_dhw_exp.nc
│       Moore_2017_599_dhw_exp.nc
│
└───spatial
│       list_gbr_reefs.csv
│       Moore.gpkg
│
└───cyclones
│       coral_cover_cyclone.csv
```