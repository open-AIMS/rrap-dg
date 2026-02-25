# Format Module

The `format` module provides specialized tools to reformat ReefMod Engine (RME) and CMIP6 datasets into standard formats used by `rrap_dg`.

## Commands

### `rme-connectivity`

Aligns RME connectivity matrices with canonical UNIQUE IDs.

```bash
uv run rrap_dg format rme-connectivity [OPTIONS]
```

### `cmip6-downscaled-dhw`

Standardizes CMIP6 statistically downscaled NetCDF DHW files.

```bash
uv run rrap_dg format cmip6-downscaled-dhw [OPTIONS]
```

### `rme-dhw`

Converts RME DHW CSVs to standardized NetCDF files.

```bash
uv run rrap_dg format rme-dhw [OPTIONS]
```

### `rme-icc`

Processes RME Initial Coral Cover (ICC) into NetCDF using spatial averaging.

```bash
uv run rrap_dg format rme-icc [OPTIONS]
```

## Alignment

A key feature of this module is the alignment of different datasets (RME, CMIP6) with the canonical spatial geopackage, ensuring that location IDs and ordering remain consistent across all data layers.
