# Development - Automating Metadata Creation

This section describes the internal logic used by `rrap_dg` to handle metadata and generate standardized `datapackage.json` files.

## 1. Formatted Datasets (`format` module)

When using the `format` module (e.g., `rme-dhw`, `rme-connectivity`), the final step of the formatting process is a call to `finalize_dataset()`.

### Metadata
For each input source (e.g., the raw RME CSVs and the canonical geopackage), the tool searches for existing metadata in the following order:

1. `metadata.json` (Provana/RRAP standard)
2. `ro-crate-metadata.json`

### `datapackage.json` Generation
The tool aggregates this information to create a `datapackage.json` for the formatted dataset. Key logic includes:

- **Provenance:** It determines if a source is a Data Store Handle or a local path.
- **Handles:** If the source is a handle (e.g., `102.100.100/711071`), the `handle` field is populated and the `path` is left blank in the resulting source entry.
- **Local Paths:** If the source is a local path, the `path` field is populated and the `handle` is left blank.

The `datapackage.json` file will then be populated with a `sources` field that describes
which datasets were used to generate the new dataset, a `contributors` field that describes
who the point of contact is for each of the source data, and a `resource` field that
contains metadata about the dataset that was generated.

## 2. Domain Packages (`template` module)

The `template build` command aggregates multiple formatted datasets into a single ADRIA-compatible Domain package.

### Build Artifacts
During the `build` process, intermediate metadata files are fetched and stored as `[resource].metadata.json`
(e.g., `spatial.metadata.json`, `dhw.metadata.json`) within their respective sub-directories.
These are used to build the final domain `datapackage.json` file.

### Aggregation Logic
The `finalize_domain_package()` function performs the following steps:

1. **Resource Documentation:** It iterates through each required resource (spatial, dhw, connectivity, icc) and documents metadata such as path and format.
2. **Metadata Extraction:** For each resource, it looks for metadata in this priority:
    - The intermediate `[resource].metadata.json` file.
    - `datapackage.json` (if the source was already a formatted dataset).
    - `metadata.json` or `ro-crate-metadata.json`.
3. **Source and Contributor Documentation:** All source datasets and contributors
   are documented in their respective fields.

## 3. Metadata Schema Support

The system is designed to be "schema-aware" and can extract information from two main formats:

- **Standard Datapackage:** Reads `sources` and `contributors` directly from an existing `datapackage.json`.
- **Provana/RRAP Metadata:** Reads fields from `dataset_info` (name, description, publisher_id) and `associations` (point_of_contact).

## 4. NetCDF Coding Standards & Conventions

To ensure output NetCDF files are fully compatible with downstream modeling frameworks (like ADRIA) and analysis libraries (like xarray):

- **Coordinate Variable Rule:** Any multi-dimensional NetCDF variables representing scenarios, locations, or timesteps **must** have corresponding coordinate variables named identically to the dimension. These coordinate variables must contain the descriptive metadata indices (e.g., GCM names for `scenarios`, unique location IDs for `locations`).
- **Backward Compatibility:** When adding coordinate variables, preserve the legacy metadata variables (e.g., `model_names` alongside `scenarios`) so that legacy code does not fail.

