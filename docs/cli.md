# CLI Reference

The `rrapdg` command-line tool is organized into several command groups.

## Degree Heating Weeks (DHW)

Generate Degree Heating Week projections using combinations of NOAA CRW data, MIROC5 projections, and RECOM patterns.

**Usage:**

```console
(rrap-dg) $ rrapdg dhw generate [cluster name] [input data directory] [output directory] [optional settings...]
```

Example:
```console
(rrap-dg) $ rrapdg dhw generate Moore C:/data_package_location C:/temp --n-sims 50 --rcps "2.6 4.5 6.0 8.5" --gen-year "2025 2100"
```

## Initial Coral Cover (ICC)

Downscale ReefMod Engine (RME) coral cover data to ADRIA format.

**Usage:**

```console
(rrap-dg) $ rrapdg coral-cover downscale-icc [rrap-dg datapackage path] [target geopackage] [output path]
```

Example:
```console
(rrap-dg) $ rrapdg coral-cover downscale-icc C:/example/rrapdg ./Moore.gpkg ./coral_cover.nc
```

## Cyclone Mortality

Generate Cyclone Mortality projections.

**Usage:**

```console
(rrap-dg) $ rrapdg cyclones generate [rrapdg datapackage path] [reefmod engine datapackage path] [output directory path]
```

## Domain Clusters

Assign locations in a geopackage to clusters using k-means clustering (Adaptive Differential Evolution).

**Usage:**

```console
(rrap-dg) $ rrapdg domain cluster [geopackage path] [output directory path]
```

Example:
```console
(rrap-dg) $ rrapdg domain cluster "C:/example/example.gpkg" "./test.gpkg"
```

## Integrated GBR Domain Generation

Generate a complete GBR-wide ADRIA Domain using a configuration file.

**Usage:**

```console
(rrap-dg) $ rrapdg GBR build-domain [OUTPUT_PARENT_DIR] [CONFIG_FILE]
```

See [GBR Domain Generation](gbr_domain.md) for detailed configuration instructions.

## RRAP M&DS Data Store

Download data from the M&DS datastore.

**Usage:**

### Download to Directory

```console
(rrap-dg) $ rrapdg data-store download [dataset id] [output directory]
```

### Download to Cache

Download a dataset to the system cache (default: `~/.cache/rrap-dg`).

```console
(rrap-dg) $ rrapdg data-store download-w-cache [dataset id] [--force]
```

## Data Package Templates

Create empty ADRIA Domain data package structures.

**Usage:**

```console
(rrap-dg) $ rrapdg template generate [output directory]
```

Example:
```console
(rrap-dg) $ rrapdg template generate ./new_domain
```