# Installation

## Prerequisites

*   Python 3.7 or higher
*   Julia (automatically managed by `juliapkg` and `juliacall`, but having it installed is recommended)

## Installing from Source

1.  Clone the repository:
    ```bash
    git clone https://github.com/unknown/rrap-dg.git
    cd rrap-dg
    ```

2.  Install the package using pip:
    ```bash
    pip install .
    ```

    For development installation (editable mode):
    ```bash
    pip install -e .
    ```

## Configuration

For interacting with the RRAP Data Store, you may need to configure your authentication credentials. The tool uses `provenaclient` for this purpose.

Create a `.env` file in your working directory or set environment variables if required by your specific deployment.
