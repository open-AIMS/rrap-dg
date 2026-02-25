# Data Store Module

The `data-store` module provides a convenient way to retrieve datasets from the RRAP M&DS Data Store.

## Commands

### `download`

Download data from the RRAP M&DS data store using a handle ID.

**Usage:**

```bash
uv run rrap_dg data-store download HANDLE_ID DEST
```

### `download-w-cache`

Download data and save it to a local cache directory. If the data is already in the cache, it returns the existing path.

**Usage:**

```bash
uv run rrap_dg data-store download-w-cache [OPTIONS] HANDLE_ID
```

**Options:**

- `--force`: Force a re-download even if the data exists in the cache.

## Configuration

The cache directory is controlled by the `DATA_STORE_CACHE_DIR` setting (default: `~/.cache/rrap-dg`).
