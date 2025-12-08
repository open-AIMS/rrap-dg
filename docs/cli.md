# CLI Reference

The `rrapdg` command-line tool is organized into several command groups.

## Global Options

*   `--help`: Show help message and exit.

## Command Groups

### `GBR`
Commands specific to Great Barrier Reef workflows.
*   `generate-domain-from-store`: Generate a full domain from data store handles or local files.
*   `format-dhw`: Format Degree Heating Week datasets.
*   `format-connectivity`: Format ReefMod Engine connectivity datasets.
*   `format-icc`: Format initial coral cover data.
*   `generate-domain-from-local`: Generate a domain from strictly local file paths.

### `domain`
General domain clustering and generation tools.
*   `cluster`: Cluster a domain based on connectivity and other metrics.

### `dhw`
Tools for processing Degree Heating Week data.
*   (See `--help` for specific subcommands)

### `cyclones`
Tools for processing cyclone mortality data.
*   (See `--help` for specific subcommands)

### `coral-cover`
Tools for downscaling and formatting initial coral cover.

### `data-store`
Interactions with the RRAP Data Store.
*   `download`: Download datasets.
*   `list`: List datasets.

### `template`
Helpers for creating data packages.
*   `generate`: Create an empty ADRIA domain data package structure.
