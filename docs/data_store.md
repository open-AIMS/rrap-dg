# Data Store Interaction

The `rrapdg` tool includes commands to interact with the RRAP M&DS Data Store, powered by Provena.

## Command Group: `data-store`

Use these commands to list, fetch, and manage datasets.

### `list`

List available items in the data store.

```bash
rrapdg data-store list
```

### `download`

Download a dataset by its handle ID.

```bash
rrapdg data-store download [HANDLE_ID] [OUTPUT_DIRECTORY]
```

*   `HANDLE_ID`: The unique identifier for the dataset (e.g., `10378.1/123456`).
*   `OUTPUT_DIRECTORY`: The local folder where files will be saved.

### `upload`

(If implemented) Upload new datasets to the store.

*Note: Check `rrapdg data-store --help` for the full list of available commands and their specific options.*
