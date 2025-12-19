# Installation

## Prerequisites

*   Python 3.11 or higher
*   Julia (automatically managed by `juliapkg` and `juliacall`, but having it installed is recommended)

## Installing from Source

1.  Clone the repository:
```bash
git clone https://github.com/open-AIMS/rrap-dg
cd rrap-dg
```

2.  **Using Conda/Mamba (Recommended)**:
    It is recommended that any development work be done in a separate environment.

```bash
# Create a new environment called rrap-dg
$ mamba create -n rrap-dg python=3.11

# Don't forget to activate the environment
$ mamba activate rrap-dg

# Install local development copy of rrap-dg
(rrap-dg) $ pip install -e .
```

3.  **Using Python venv**:
    Alternatively, you can use a traditional python venv.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Initial Setup

The first time `rrapdg` is run, it will go through an initial set up process. Run the help command to trigger the setup.

```bash
rrapdg --help
```

## Configuration (Environment Variables)

This project uses Pydantic's `BaseSettings` to manage configuration. You can override default settings using a `.env` file or environment variables.

### Creating a .env File

1. Create a file named `.env` in the root directory of the project.
2. Add your custom settings to this file using the following format:

```
PROVENA_DOMAIN=your.provena.domain.com
PROVENA_REALM_NAME=provena
PROVENA_CLIENT_ID=automated-access
```

### Available Settings

- `PROVENA_DOMAIN`: The Provena deployment to target (default: "mds.gbrrestoration.org")
- `PROVENA_REALM_NAME`: The Keycloak realm name (default: "rrap")
- `PROVENA_CLIENT_ID`: The Keycloak client ID (default: "automated-access")
