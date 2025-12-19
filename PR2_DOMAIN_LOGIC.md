# PR 2: Domain Builder & Formatters

## Description
This PR implements the core business logic for the new GBR Domain Generator. It builds upon the infrastructure from PR #1 to orchestrate the creation of ADRIA-compatible data packages.

## Key Changes
- **Domain Builder (`rrap_dg/format_gbr/domain_builder.py`):**
  - The central orchestrator that reads a TOML configuration, resolves sources using `SourceManager`, and delegates tasks to specific formatters.
  - Automatically generates `datapackage.json` and a `README.md` for the generated domain.
- **Formatters (`rrap_dg/format_gbr/formatters.py`):**
  - Implemented a pluggable `Formatter` architecture.
  - **Connectivity:** `RMEConnectivityFormatter` aligns RME connectivity matrices with canonical domain IDs.
  - **DHW:** `DHWFormatter` and `RMEDHWFormatter` handle NetCDF and CSV-based Degree Heating Week projections, including extracting climate model names for documentation.
  - **Coral Cover:** `GBRICCFormatter` interfaces with Julia scripts to downscale Initial Coral Cover.
  - **Utilities:** `MoveFileFormatter` for simple file operations.
- **Julia Integration:**
  - Updated `rrap_dg/initial_coral_cover/icc.jl` to support the new formatting workflow.
- **CLI (`rrap_dg/format_gbr/format.py` & `main.py`):**
  - Added the `rrap_dg GBR build-domain` command to trigger the process.

## Motivation
This feature allows for a configuration-driven approach to generating complex domain datasets, replacing rigid scripts with a flexible, modular system.

## Dependencies
- Depends on PR #1 (`feature/provena-infra`).
