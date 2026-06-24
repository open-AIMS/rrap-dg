# Template Module

The `template` module assists in creating and building standardized ADRIA Domain data packages.

## Commands

### Command: generate

Scaffolds an empty ADRIA Domain directory structure.

**Usage:**

```bash
uv run rrapdg template generate TEMPLATE_PATH
```

### Command: build

Builds an ADRIA Domain by fetching datasets from handles or local paths into the standardized structure.
Sources and file lists are configured via a TOML config file.

**Usage:**

```bash
uv run rrapdg template build CONFIG_PATH OUTPUT_PATH
```

**Arguments:**

- `CONFIG_PATH`: Path to a TOML configuration file.
- `OUTPUT_PATH`: Path to create the domain directory.

### Configuration File (TOML)

The `build` command requires a TOML configuration file. The file should specify the domain name and the sources for each required dataset. Optional file lists can be provided for each source.

**Example `config.toml`:**

```toml
domain_name = "GBR_TEST"

[spatial]
source = "102.100.100/711118"
files = ["rrap_canonical_2025-07-15-T10-48-29.gpkg"]

[dhw]
source = "path/to/local/dhw"
# No 'files' list means all files are fetched.

[connectivity]
source = "102.100.100/123456"

[icc]
source = "102.100.100/789012"
files = ["coral_cover.nc"]

[cyclones]
# Optional
source = "102.100.100/112233"

[waves]
# Optional
source = "path/to/local/waves"
```

## Implementation Details

- Automatically aggregates metadata from source datasets.
- Generates a `datapackage.json` compliant with the ADRIA specification.
- Renames the spatial geopackage to match the domain version tag (e.g., `GBR_TEST_2026-03-09_v080.gpkg`).
- Correctly handles provenance by setting the `handle` for datastore datasets and the `path` for local files.
