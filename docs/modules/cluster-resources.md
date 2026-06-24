# Cluster Resources

This page documents the standard data package structures, available spatial cluster geopackages, and the corresponding RECOM (Regional Ecological Oceanography Model) marine heatwave datasets.

---

## Standard Data Package Layout

The `rrap_dg` tool relies on a standardized directory structure for its source data packages. This ensures that all necessary data layers are available for generating environmental projections and mortality scenarios.

For example, a standard data package (such as the Moore Reef Cluster available on the [RRAP M&DS data store](https://data.mds.gbrrestoration.org/dataset/102.100.100/481718?view=overview)) follows this layout:

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

### Module Requirements

Different modules require specific parts of this data package:

- **`dhw` module**: Requires `MIROC5`, `NOAA`, `RECOM`, and `spatial` directories.
- **`cyclones` module**: Requires the `cyclones` directory.
- **`coral-cover` module**: Requires the `spatial` directory for site alignment.

---

## Available Clusters & Geopackages

The following table lists the spatial cluster geopackage datasets used for domain definitions.

| Cluster Name | IS Store Handle ID |
| :--- | :--- |
| `Moore` | [`102.100.100/481718`](https://hdl.handle.net/102.100.100/481718) |
| `Davies` | [`102.100.100/713249`](https://hdl.handle.net/102.100.100/713249)|
| `Lizard` | [`102.100.100/713245`](https://hdl.handle.net/102.100.100/713245) |
| `Heron` | [`102.100.100/713247`](https://hdl.handle.net/102.100.100/713247) |

---

## Available RECOM Datasets

Each cluster requires corresponding RECOM files containing spatial marine heatwave patterns. Ensure the filenames or patterns match the expected structure:

| Cluster Name | IS Store Handle ID | Expected File Pattern |
| :--- | :--- | :--- |
| `Moore` | [`102.100.100/481718`](https://hdl.handle.net/102.100.100/481718) | `*Moore*_*_dhw*.nc` |
| `Davies` | [`102.100.100/485144`](https://hdl.handle.net/102.100.100/485144) | `*Cairns*_*_dhw*.nc` |
| `Lizard` | [`102.100.100/485092`](https://hdl.handle.net/102.100.100/485092) | `*Lizard*_*_dhw*.nc` |
| `Heron` | [`102.100.100/484974`](https://hdl.handle.net/102.100.100/484974) | `*Heron*_*_dhw*.nc` |

!!! note
    During DHW generation, the generator automatically globs the RECOM directory using the pattern `*{cluster_name}*_*_dhw*.nc` to find the marine heatwave spatial maps.
