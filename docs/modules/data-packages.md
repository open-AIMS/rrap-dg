# Data Package Structure

The `rrap_dg` tool relies on a standardized directory structure for its source data packages. This structure ensures that all necessary data layers are available for generating environmental projections and mortality scenarios.

## Standard Directory Layout

Generators for cluster-scale DHWs and Cyclones expect the following formats and a data
package for Moore Reef Cluster can be found on the [RRAP M&DS data store](https://data.mds.gbrrestoration.org/dataset/102.100.100/481718?view=overview)

```bash
Moore_rrapdg_2023-01-24/
│   datapackage.json
│   README.md
│
├───MIROC5/              # DHW projections from MIROC5
│       GBR_maxDHW_MIROC5_rcp26_2021_2099.csv
│
├───NOAA/                # Historical DHW satellite data from NOAA
│       GBR_dhw_hist_noaa.nc
│
├───RECOM/               # Regional heatwave patterns
│       Moore_2015_585_dhw_exp.nc
│
├───spatial/             # Geopackage and reef metadata
│       list_gbr_reefs.csv
│       Moore.gpkg
│
└───cyclones/            # Cyclone mortality data
        coral_cover_cyclone.csv
```

## Module Requirements

Different modules require specific parts of this data package:

- **`dhw` module**: Requires `MIROC5`, `NOAA`, `RECOM`, and `spatial` directories.
- **`cyclones` module**: Requires the `cyclones` directory.
- **`coral-cover` module**: Requires the `spatial` directory for site alignment.
