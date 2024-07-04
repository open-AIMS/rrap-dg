# RRAP Data Generators

Provides a single command-line interface to generate data sets for use with [ADRIA](https://github.com/open-AIMS/ADRIA.jl) and the RRAP program.


[![PyPI - Version](https://img.shields.io/pypi/v/rrap-dg.svg)](https://pypi.org/project/rrap-dg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rrap-dg.svg)](https://pypi.org/project/rrap-dg)

-----

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
  - [Connectivity data](#connectivity-data)
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
(rrap-dg) $ rrapdg data_store download [dataset id] [output directory]
```

For example, to download and save the dataset with id "102.100.100/602432" in the current directory:

```console
(rrap-dg) $ rrapdg data_store download 102.100.100/602432 .
```

Semantically, the command is to download from a *source* to a *destination*.

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

## License

`rrap-dg` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
