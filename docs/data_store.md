# Data Store Interaction

The `rrapdg` tool includes commands to interact with the RRAP M&DS Data Store, powered by Provena.

## Command Group: `data-store`

Use these commands to fetch datasets.

### `download`

Download a dataset by its handle ID.

```bash
rrapdg data-store download [HANDLE_ID] [OUTPUT_DIRECTORY]
```

*   `HANDLE_ID`: The unique identifier for the dataset (e.g., `10378.1/123456`).
*   `OUTPUT_DIRECTORY`: The local folder where files will be saved.

*Note: Check `rrapdg data-store --help` for the full list of available commands and their specific options.*
