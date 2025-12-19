# PR 1: Provena Infrastructure & Caching

## Description
This PR introduces the foundational infrastructure required to efficiently manage data source retrieval from the RRAP M&DS Data Store (Provena). It focuses on configuration management and caching mechanisms to prevent redundant downloads.

## Key Changes
- **Configuration Update (`rrap_dg/config.py`):** 
  - Added `data_store_cache_dir` to the settings. This defines a persistent location (`~/.cache/rrap-dg` by default) where downloaded datasets are stored.
- **Source Manager (`rrap_dg/format_gbr/source_manager.py`):**
  - Implemented the `SourceManager` class.
  - Handles the logic of resolving a source "handle" (e.g., a dataset ID) to a local directory.
  - **Caching Logic:** checks if a dataset is already present in the cache directory before attempting a download via the `provenaclient`.
- **Config Models (`rrap_dg/format_gbr/config_model.py`):**
  - Added Pydantic models (`SourceConfig`) to validate source definitions (ensuring either a `handle` or `path` is provided).

## Motivation
Previously, data retrieval might have been ephemeral or required manual management. This infrastructure ensures that subsequent domain generation runs are faster and more reliable by reusing downloaded assets.

## Dependencies
- Base PR. Target: `main`.
