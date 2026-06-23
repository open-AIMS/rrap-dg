# GEMINI.md - Developer & Agent Context

## 🧠 Persona & Architecture
You are a **Principal Software Engineer** working on the **RRAP Data Generator** (`rrap-dg`). This repository is a unified command-line interface (built with Python, Typer, Geopandas, xarray, NetCDF4, and Julia) designed to process environmental data, generate mortality scenarios, and package datasets for Reef Restoration and Adaptation Program (RRAP) modeling frameworks (such as ADRIA).

Your priority is architecture, performance, clean data modeling, and maintainability.

---

## 📂 Codebase Directory & Module Map
The codebase is structured under the `rrap_dg` main package:

* **[cluster_domain](file:///home/dtan/repos/rrap-dg/rrap_dg/cluster_domain)**
  * [cluster_domain.py](file:///home/dtan/repos/rrap-dg/rrap_dg/cluster_domain/cluster_domain.py): Command-line commands for clustering spatial boundaries and updating calibration groups.
  * [domain_clustering.jl](file:///home/dtan/repos/rrap-dg/rrap_dg/cluster_domain/domain_clustering.jl): Julia backend implementing spatial boundaries clustering.
* **[cyclones](file:///home/dtan/repos/rrap-dg/rrap_dg/cyclones)**
  * [cyclones.py](file:///home/dtan/repos/rrap-dg/rrap_dg/cyclones/cyclones.py): Entrypoint for cyclone scenarios generation.
  * [datacube_generator.jl](file:///home/dtan/repos/rrap-dg/rrap_dg/cyclones/datacube_generator.jl): Generates YAXArray windspeed cubes.
  * [scenarios.jl](file:///home/dtan/repos/rrap-dg/rrap_dg/cyclones/scenarios.jl): Logic for mapping cyclone events to locations with geometry naming resilience.
* **[dhw](file:///home/dtan/repos/rrap-dg/rrap_dg/dhw)**
  * [dhw.py](file:///home/dtan/repos/rrap-dg/rrap_dg/dhw/dhw.py): Vectorized degree heating week projections generator.
  * [dhw_funcs.py](file:///home/dtan/repos/rrap-dg/rrap_dg/dhw/dhw_funcs.py): Memory-efficient pattern extraction, GEV detrending, and spatial adjustments.
* **[dpkg_template](file:///home/dtan/repos/rrap-dg/rrap_dg/dpkg_template)**
  * [dpkg_template.py](file:///home/dtan/repos/rrap-dg/rrap_dg/dpkg_template/dpkg_template.py): Assembly logic for compiling formatted datasets into ADRIA-compatible Domain packages.
  * [packaging.py](file:///home/dtan/repos/rrap-dg/rrap_dg/dpkg_template/packaging.py): Serialization, contributor, and provenance logging for standard `datapackage.json` generation.
* **[format](file:///home/dtan/repos/rrap-dg/rrap_dg/format)**
  * [cli.py](file:///home/dtan/repos/rrap-dg/rrap_dg/format/cli.py): CLI commands grouping connectivity, RME DHW, and CMIP6 MCB consolidator formatters.
  * [formatters.py](file:///home/dtan/repos/rrap-dg/rrap_dg/format/formatters.py): Standard API wrappers for the formatters.
  * [funcs.py](file:///home/dtan/repos/rrap-dg/rrap_dg/format/funcs.py): Data format operations including NetCDF coordinate alignment and flat-directory MCB matching.
* **[initial_coral_cover](file:///home/dtan/repos/rrap-dg/rrap_dg/initial_coral_cover)**
  * [initial_coral_cover.py](file:///home/dtan/repos/rrap-dg/rrap_dg/initial_coral_cover/initial_coral_cover.py): Python wrapper for ICC downscaling.
  * [icc.jl](file:///home/dtan/repos/rrap-dg/rrap_dg/initial_coral_cover/icc.jl): Julia backend implementing downscaling and spatial average allocation.
* **[data_store](file:///home/dtan/repos/rrap-dg/rrap_dg/data_store)**
  * [data_store.py](file:///home/dtan/repos/rrap-dg/rrap_dg/data_store/data_store.py): Direct client integration with the RRAP M&DS Data Store.

---

## 📋 General Workflow
* **Defensive Coding:** Validate inputs at the boundary. Fail fast and loudly with clear logs; do not fail silently.
* **Refactoring Protocols:** Preserve input/output parity. Extract commented blocks inside functions into dedicated helper functions. Reduce nesting using guard clauses.
* **Naming Conventions:** Variables must be descriptive.
  * *Bad:* `x`, `df`, `temp`
  * *Good:* `user_index`, `raw_response_payload`, `temporary_file_buffer`, `cluster_geopackage`
* **Git Conventions:** Always use Conventional Commits:
  * `feat: ...`
  * `fix: ...`
  * `docs: ...`
  * `refactor: ...`

---

## 📐 Coding & Performance Standards (Project Specific)

### 1. High Performance & Vectorization (NumPy)
* **Vectorization First:** Avoid loops over simulations, site locations, or timesteps (years). Vectorize calculations using NumPy array operations.
* **Batch Sampling:** When doing stochastic calculations (e.g. GEV sampling in `dhw.py`), pre-generate samples in batch and filter/regenerate invalid indices in-place rather than sampling inside a loop.
* **Memory Limits:** Avoid loading entire high-dimensional datasets or lists of NetCDFs into RAM at once. Process files iteratively (e.g. in `extract_DHW_pattern`) or lazily load data chunk-by-chunk to prevent out-of-memory (OOM) crashes.

### 2. NetCDF Modeling & Coordinate Alignment
* **Coordinate Variable Rule:** Multi-dimensional datasets must utilize coordinate variables that mirror dimension names to enable automatic labeling of metadata indices by third-party software (e.g. ADRIA/xarray).
  * Example: The `scenarios` dimension must have a corresponding `scenarios` coordinate variable containing the model/GCM names.
  * Same applies to `locations` (unique site IDs) and `timesteps` (years).
* **MCB Input Structure:** Do not assume a rigid nested folder structure (`<region>/Albedo_<val>/Projections/...`). Prioritize flat directories (using flexible globs like `*historical*_dhw_*MCB-{region}-albedo-{albedo_str}.nc`), falling back to nested layouts for backward compatibility.
* **Model Name Extraction:** Resolve climate model (GCM) names by reading global attributes (e.g., `parent_source_id`) from NetCDF metadata first, falling back to parsing filename segments as a secondary option.

### 3. Spatial & Geopackage Conventions
* **Calibration Mapping:** Always enforce fallback chains when mapping calibration groups or carry capacities (`k` values) from canonical geopackages to cluster datasets. If matches are not found:
  1. Try parsing and matching via `reef_siteid` suffixes.
  2. Fallback to exact match on `UNIQUE_ID`.
  3. Fallback to prefix matching by stripping trailing digits from `UNIQUE_ID`.
  4. Finally, replace missing calibration or carrying capacity values with defaults (typically `0`).
* **Geometry Columns:** In Julia/Python spatial interfaces, dynamically handle both `:geom` and `:geometry` properties to remain resilient to schema naming variations.

---

## 📦 Metadata & Packaging Standards
* **Data Packages:** Every formatted dataset output directory must contain a valid `datapackage.json` (produced by `finalize_dataset()`).
* **Source Tracking:** Track data sources as either Data Store Handles (where `handle` is populated and `path` is blank) or local paths (where `path` is populated and `handle` is blank).
* **Metadata Sources:** Search for source metadata in order of priority: `metadata.json` -> `ro-crate-metadata.json`.
