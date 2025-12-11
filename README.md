# RRAP Data Generators

Provides a single command-line interface to generate data sets for use with [ADRIA](https://github.com/open-AIMS/ADRIA.jl) and the RRAP program.

[![PyPI - Version](https://img.shields.io/pypi/v/rrap-dg.svg)](https://pypi.org/project/rrap-dg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rrap-dg.svg)](https://pypi.org/project/rrap-dg)

# Warning: requires Python >= 3.11 

---

**Table of Contents**

- [RRAP Data Generators](#rrap-data-generators)
  - [Installation](#installation)
    - [From PyPI (TODO)](#from-pypi-todo)
    - [Dev version](#dev-version)
    - [For Development](#for-development)
  - [rrap-dg Data Packages](#rrap-dg-data-packages)
  - [Domain Template](#domain-template)
  - [Degree Heating Weeks (DHW) projections](#degree-heating-weeks-dhw-projections)
  - [Initial Coral Cover](#initial-coral-cover)
  - [Cyclone Mortality projections](#cyclone-mortality-projections)
  - [RRAP M\&DS data store interface](#rrap-mds-data-store-interface)
  - [Wave data](#wave-data)
  - [Domain clusters](#domain-clusters)
  - [License](#license)

## Installation

TODO: Standalone executable.

### From PyPI (TODO)

```console
pip install rrap-dg
```

### Dev version

```console
pip install git+https://github.com/open-AIMS/rrap-dg
```

### For Development

Clone the repository, and navigate to the project folder.

```bash
git clone https://github.com/open-AIMS/rrap-dg
cd rrap_dg
```

It is recommended that any development work be done in a separate environment.

Here, [`mamba`](https://mamba.readthedocs.io/en/latest/) is used to create a local `conda` environment.

```bash
# Create a new environment called rrap-dg
$ mamba create -n rrap-dg python=3.11

# Don't forget to activate the environment
$ mamba activate rrap-dg

# Install local development copy of rrap-dg
(rrap-dg) $ pip install -e .
```

Note: The first time `rrapdg` is run, it will go through an initial set up process.

Run the help command to trigger the setup.

```bash
(rrap-dg) $ rrapdg --help
```

## Python venv setup

Alternatively, you can use a traditional python venv. For example

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Overriding Default Settings

This project uses Pydantic's `BaseSettings` to manage configuration. While default values are provided, you can easily override these settings using a `.env` file.

### Creating a .env File

1. Create a file named `.env` in the root directory of the project.
2. Add your custom settings to this file using the following format, noting all values are optional:

```
PROVENA_DOMAIN=your.provena.domain.com
PROVENA_REALM_NAME=provena
PROVENA_CLIENT_ID=automated-access
```

### Available Settings

The following settings can be overridden:

- `PROVENA_DOMAIN`: The Provena deployment to target (default: "mds.gbrrestoration.org")
- `PROVENA_REALM_NAME`: The Keycloak realm name (default: "rrap")
- `PROVENA_CLIENT_ID`: The Keycloak client ID (default: "automated-access")

## rrap-dg Data Packages

The rrap-dg Data Packages are used as inputs by DHW and Cyclone Mortality data generators.
To generate DHW data cubes, the folders `MIROC5`, `NOAA`, `RECOM` and `spatial` are required. To
generate the coral mortality projections due to cyclones, the folder `cyclone_mortality` is required.

The data package should be named with the following convention:

`[cluster name]_rrapdg_[YYYY-MM-DD]`

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

The most recent data package is available on the RRAP IS Data store:
https://hdl.handle.net/102.100.100/481718

## Domain Template

Create an empty ADRIA Domain to be filled with data.

```console
(rrap-dg) $ rrapdg template generate [directory]
```

**TODO:** Package an ADRIA Domain with data from the M&DS data store.

```console
(rrap-dg) $ rrapdg template package [directory] [spec]
```

Where spec points to a json file defining handle IDs for each dataset to be downloaded
from the M&DS data store.

## Degree Heating Weeks (DHW) projections

Generate Degree Heating Week projections using combinations of

- NOAA Coral Reef Watch (CRW version 3.1) satellite data
- MIROC5 RCP projections (2021 - 2099)
- RECOM spatial multi-marine heat wave patterns

This work was ported to Python from the original MATLAB developed by Dr. Veronique Lago and modified by Chinenye Ani in MATLAB.

Usage:

```console
(rrap-dg) $ rrapdg dhw generate [cluster name] [input data directory] [output directory] [optional settings...]
```

For example, with default values shown for optional settings:

```console
(rrap-dg) $ rrapdg dhw generate Moore C:/data_package_location C:/temp --n-sims 50 --rcps "2.6 4.5 6.0 8.5" --gen-year "2025 2100"
```

Note that the output directory is assumed to already exist.

The expected data package are detailed [here](https://github.com/open-AIMS/rrap-dg?tab=readme-ov-file#rrap-dg-data-packages)

## Initial Coral Cover

Initial coral cover data is downscaled from ReefMod Engine (RME) data.
The current process is compatible with ReefMod or RME v1.0.x datasets or the rrap-dg
data package.

```console
(rrap-dg) $ rrapdg coral-cover downscale-icc [rrap-dg datapackage path] [target geopackage] [output path]
```

For example, to downscale RME data for the Moore cluster defined by a geopackage:

```console
(rrap-dg) $ rrapdg coral-cover downscale-icc C:/example/rrapdg ./Moore.gpkg ./coral_cover.nc
(rrap-dg) $ rrapdg coral-cover downscale-icc C:/example/rme_dataset ./Moore.gpkg ./coral_cover.nc
```

A set of initial cover files can be created using a TOML file:

```console
(rrap-dg) $ rrapdg coral-cover downscale-icc [rrap-dg datapackage path] [target geopackage] [output directory] [TOML file]
```

The output path is assumed to exist.

```console
(rrap-dg) $ rrapdg coral-cover bin-edge-icc C:/example/rrapdg ./Moore.gpkg ./icc_files ./bin_edges.toml
```

This will create a set of netCDFs in the `icc_files` directory using the bin edges defined
in the TOML file.

The format of the TOML file is:

```TOML
name_of_file = [
    [values, for, each, size class],
	[rows, are, functional, groups],
	[cols, are size, classes]
]
```

Note that ReefMod represents arborescent Acropora, whereas CoralBlocks does not.
Hence the first line is set to 0.0.

A full example:

```TOML
bin_edge_1 = [
	[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
	[5.0, 7.5, 10.0, 20.0, 40.0, 100.0, 150.0],
	[5.0, 7.5, 10.0, 20.0, 35.0, 50.0, 100.0],
	[5.0, 7.5, 10.0, 15.0, 20.0, 40.0, 50.0],
	[5.0, 7.5, 10.0, 20.0, 40.0, 50.0, 100.0],
	[5.0, 7.5, 10.0, 20.0, 40.0, 50.0, 100.0]
]

bin_edge_2 = [
	[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
	[4.0, 7.5, 10.0, 20.0, 40.0, 100.0, 150.0],
	[4.0, 7.5, 10.0, 20.0, 35.0, 50.0, 100.0],
	[4.0, 7.5, 10.0, 15.0, 20.0, 40.0, 50.0],
	[4.0, 7.5, 10.0, 20.0, 40.0, 50.0, 100.0],
	[4.0, 7.5, 10.0, 20.0, 40.0, 50.0, 100.0]
]

bin_edge_3 = [
	[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
	[5.0, 7.5, 10.0, 20.0, 40.0, 100.0, 100.0],
	[5.0, 7.5, 10.0, 20.0, 35.0, 50.0, 120.0],
	[5.0, 7.5, 10.0, 15.0, 20.0, 40.0, 60.0],
	[5.0, 7.5, 10.0, 20.0, 40.0, 50.0, 110.0],
	[5.0, 7.5, 10.0, 20.0, 40.0, 50.0, 120.0]
]
```

Using the above will create files named `bin_edge_1`, `bin_edge_2`, ..., etc.

## Cyclone Mortality projections

Generate Cyclone Mortality projections using data from

- Fabricius, Katharina E., et al. "Disturbance gradients on inshore and offshore coral reefs caused by a severe tropical cyclone." Limnology and Oceanography 53.2 (2008): 690-704.
- ReefMod Engine data set

The mortality regression model was ported from an R script written by Dr. Vanessa Haller, intended for use with the C~Scape coral ecosystem model.

Usage:

```console
(rrap-dg) $ rrapdg cyclones generate [rrapdg datapackage path] [reefmod engine datapackage path] [output directory path]
```

The output directory is assumed to already exist.

## RRAP M&DS data store interface

Download data from M&DS datastore

```console
(rrap-dg) $ rrapdg data-store download [dataset id] [output directory]
```

For example, to download and save the dataset with id "102.100.100/602432" in the current directory:

```console
(rrap-dg) $ rrapdg data-store download 102.100.100/602432 .
```

Semantically, the command is to download from a _source_ to a _destination_.

**TODO: Uploading/submitting datasets.**

## Wave data

TODO

## Domain clusters

Assign each location in a geopackage file to a cluster using k-means clustering.
The cluster a location is a member of is indicated by a new column named `cluster_id`.
Results are outputted to a new geopackage file saved to the user-indicated location.

The number of clusters are determined by optimizing for a high Silhouette score with
Adaptive Differential Evolution (`adaptive_de_rand_1_bin_radiuslimited()` in
[BlackBoxOptim.jl](https://github.com/robertfeldt/BlackBoxOptim.jl)).

```console
(rrap-dg) $ rrapdg domain cluster [geopackage path] [output directory path]

# Example
(rrap-dg) $ rrapdg domain cluster "C:/example/example.gpkg" "./test.gpkg"
```

The method reports a "Best candidate", the _floor_ of which indicates the identified
optimal number of clusters.

## GBR-wide Domain Data

Format previously existing DHW and connectivity data into the format used in ADRIA.jl
domains.

### DHWs

The only supported DHW dataset is the [statistically downscaled Climate projections
(CMIP6)](https://data.mds.gbrrestoration.org/dataset/102.100.100/705397?view=overview) that
were aligned with the canonical reefs geopackage.

```console
(rrap-dg) $ rrapdg GBR format-dhw [DHW path] [output directory path] [optional settings...]
```
For example, with default settings
```console
(rrap-dg) $ rrapdg GBR format-dhw "C:/example/dhws" "C:/temp" --rcps "2.6 4.5 7.0 8.5" --timeframe "2025 2099"
```

### Connectivity

The only supported connectivity dataset is the connectivity files contained in the [ReefMod
Engine](https://data.mds.gbrrestoration.org/dataset/102.100.100/708667?view=overview) and
requires the [canonical reefs geopackage](https://github.com/gbrrestoration/canonical-reefs)
to align locations and label dimensions.

```console
(rrap-dg) $ rrapdg GBR format-connectivity [ReefMod Engine Path] [Canonical Reefs Path] [Output Directory path]
```

### Initial Coral Cover

The only supported initial cover dataset file is the connectivity files contained in the [ReefMod
Engine](https://data.mds.gbrrestoration.org/dataset/102.100.100/708667?view=overview).

```console
(rrap-dg) $ rrapdg GBR format-icc [ReefMod Engine Path] [Canonical Path] [Output Path]
```

## Integrated GBR Domain Generation

This command facilitates the generation of a complete GBR-wide ADRIA Domain by consolidating data from various sources, either from the RRAP M&DS Data Store via handle IDs or from local file paths. It supports configuration through a TOML file, allowing for flexible and centralized management of input parameters.

Usage:

```console
(rrap-dg) $ rrapdg GBR generate-domain-from-store [OUTPUT_PARENT_DIR] [DOMAIN_NAME] --config [CONFIG_FILE]
```

*   `OUTPUT_PARENT_DIR`: The parent directory where the generated domain folder will be created.
*   `DOMAIN_NAME`: A short name for the domain (e.g., "GBR").

The domain will be saved in a new directory named `<DOMAIN_NAME>_YYYY-MM-DD_v<VERSION>` within the `OUTPUT_PARENT_DIR`.

### Configuration File (TOML) Example

All domain parameters must be specified in a TOML configuration file.

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

[waves]
# handle = "10378.1/WAVE_HANDLE"
path = "/local/path/to/wave_data"
description = "Description of wave data"

[cyclones]
# handle = "10378.1/CYCLONE_HANDLE"
path = "/local/path/to/cyclone_data"
description = "Description of cyclone data"
```

## License

`rrap-dg` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
