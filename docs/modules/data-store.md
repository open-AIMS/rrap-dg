# Data Store Module

The `data-store` module provides tools to interact with the RRAP M&DS Data Store.

## Commands

### `download`

Download all files from a dataset in the RRAP M&DS data store using a handle ID.

**Usage:**

```bash
uv run rrapdg data-store download HANDLE_ID DEST
```

### `download-w-cache`

Download all files from a dataset and save them to a local cache directory. If the data is already in the cache, it returns the existing path.

**Usage:**

```bash
uv run rrapdg data-store download-w-cache [OPTIONS] HANDLE_ID
```

**Options:**

- `--force`: Force a re-download even if the data exists in the cache.

### `download-file`

Download a specific file or folder from a dataset.

**Usage:**

```bash
uv run rrapdg data-store download-file HANDLE_ID S3_PATH DEST
```

**Arguments:**

- `HANDLE_ID`: The dataset handle ID.
- `S3_PATH`: The relative path of the file or folder within the dataset.
- `DEST`: The destination directory.

### `list-files`

List all files in a dataset.

**Usage:**

```bash
uv run rrapdg data-store list-files HANDLE_ID
```

## Configuration

The cache directory is controlled by the `DATA_STORE_CACHE_DIR` setting (default: `~/.cache/rrap-dg`).
To use the datastore module, the Provana environment must be correctly configured via environment variables.
This is mainly for use in development where you may be continuously downloading the same
file.
