# Template Module

The `template` module assists in creating and building standardized ADRIA Domain data packages.

## Commands

### `generate`

Scaffolds an empty ADRIA Domain directory structure.

**Usage:**

```bash
uv run rrap_dg template generate TEMPLATE_PATH
```

### `build`

Builds an ADRIA Domain by fetching datasets from handles or local paths into the standardized structure.

**Usage:**

```bash
uv run rrap_dg template build [OPTIONS] OUTPUT_PATH
```

**Required Options:**

- `--spatial-source TEXT`: Handle ID or local path for Spatial data.
- `--dhw-source TEXT`: Handle ID or local path for DHW data.
- `--connectivity-source TEXT`: Handle ID or local path for Connectivity data.
- `--icc-source TEXT`: Handle ID or local path for Initial Coral Cover data.

**Optional Options:**

- `--cyclones-source TEXT`: Source for Cyclones data.
- `--waves-source TEXT`: Source for Waves data.
- `--domain-name TEXT`: Name for the generated package (default: "GBR").

## Implementation Details

- Automatically aggregates metadata from source datasets.
- Generates a `datapackage.json` compliant with the ADRIA specification.
