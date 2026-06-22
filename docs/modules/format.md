# Format Module

The `format` module provides specialized tools to reformat ReefMod Engine (RME) and CMIP6 datasets into standard formats used by `rrap_dg`.

## Commands

### Command: rme-connectivity

Aligns RME connectivity matrices with canonical UNIQUE IDs.

```bash
uv run rrap_dg format rme-connectivity [OPTIONS]
```

### Command: cmip6-downscaled-dhw

Standardizes CMIP6 statistically downscaled NetCDF DHW files.

```bash
uv run rrap_dg format cmip6-downscaled-dhw [OPTIONS]
```

### Command: rme-dhw

Converts RME DHW CSVs to standardized NetCDF files.

```bash
uv run rrap_dg format rme-dhw [OPTIONS]
```

### Command: rme-icc

Processes RME Initial Coral Cover (ICC) into NetCDF using spatial averaging.

```bash
uv run rrap_dg format rme-icc [OPTIONS]
```

### Command: cmip6-consolidated-mcb

Consolidates raw Marine Cloud Brightening (MCB) NetCDF files into a single multi-dimensional 5D NetCDF (one file per SSP/RCP) with historical prepend.

```bash
uv run rrap_dg format cmip6-consolidated-mcb [OPTIONS]
```

**Options:**

- `--input-path TEXT`: Path to root of raw MCB NetCDF files. [Required]
- `--output-path TEXT`: Output directory. [Required]
- `--region TEXT`: Region name (e.g. 'Cairns' or 'GBR'). [Required]
- `--hist-timeframe TEXT`: Historical timeframe 'YYYY YYYY' (default: "2007 2014").
- `--proj-timeframe TEXT`: Projection timeframe 'YYYY YYYY' (default: "2015 2100").

### Command: cmip6-mcb-prepend

Consolidates raw MCB NetCDFs into 3D NetCDFs with historical data prepended for a specific albedo and duration.

```bash
uv run rrap_dg format cmip6-mcb-prepend [OPTIONS]
```

**Options:**

- `--input-path TEXT`: Path to root of raw MCB NetCDF files. [Required]
- `--output-path TEXT`: Output directory. [Required]
- `--region TEXT`: Region name (e.g. 'Cairns' or 'GBR'). [Required]
- `--albedo TEXT`: Albedo value (e.g. 0.2, 0.3). (default: "0.3")
- `--mcb-duration INTEGER`: MCB duration in days (0, 50, 100, 150). (default: 150)
- `--hist-timeframe TEXT`: Historical timeframe 'YYYY YYYY' (default: "2007 2014").
- `--proj-timeframe TEXT`: Projection timeframe 'YYYY YYYY' (default: "2015 2100").


## Alignment

A key feature of this module is the alignment of different datasets (RME, CMIP6) with the canonical spatial geopackage, ensuring that location IDs and ordering remain consistent across all data layers.
