# RRAP Data Generators

Provides a single command-line interface to generate data sets for use with [ADRIA](https://github.com/open-AIMS/ADRIA.jl) and the RRAP program.


[![PyPI - Version](https://img.shields.io/pypi/v/rrap-dg.svg)](https://pypi.org/project/rrap-dg)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rrap-dg.svg)](https://pypi.org/project/rrap-dg)

-----

**Table of Contents**

- [Installation](#installation)
- [Degree Heating Weeks](#DHW)
- [License](#license)

## Installation

TODO: Standalone executable.

### From PyPI (TODO)

```console
pip install rrap-dg
```

### Dev version

```console
pip install git+https://github.com/open-AIMS/rrap_dg
```

### For Development


Clone the repository, and navigate to the project folder.

```bash
git clone https://github.com/open-AIMS/rrap_dg
cd rrap_dg
```

It is recommended that any development work be done in a separate environment.

Here, [`mamba`](https://mamba.readthedocs.io/en/latest/) is used to create a local `conda` environment.

```bash
# Assume Windows platform
mamba create -n rrap-dg --file win_env.yml
```

For ease of use, install `rrap-dg` as a local editable copy with `pip`.

```bash
pip install -e .
```

## Degree Heating Weeks

Generate Degree Heating Week projections using combinations of 

- NOAA Coral Reef Watch (CRW version 3.1) satellite data
- MIROC5 RCP projections (2021 - 2099)
- RECOM spatial multi-marine heat wave patterns

This work was ported to Python from the original MATLAB developed by Dr. Veronique Lago and modified by Chinenye Ani in MATLAB.

Usage:

```console
rrapdg dhw generate [input data directory] [output directory] [optional settings...]
```

For example, with default values shown for optional settings:

```console
rrapdg dhw generate C:/data_package_location C:/temp --n-sims 50 --rcps "2.6 4.5 6.0 8.5" --proj-year "2025 2100"
```

Note that the output directory is assumed to already exist.


### Expected Datapackage Structure

Datapackages should be named with the following convention:

`[cluster name]_DHW_[YYYY-MM-DD]`

An example for a hypothetical Moore dataset

```
Moore_DHW_2023-01-24
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
        list_gbr_reefs.csv
        Moore.gpkg
```


## Connectivity data

TODO

## Wave data

TODO

## License

`rrap-dg` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
