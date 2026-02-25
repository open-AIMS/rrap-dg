# AIMS-RRAP Data Generator

The **RRAP Data Generator** (`rrap_dg`) is a command-line tool designed to generate and format data for the Reef Restoration and Adaptation Program (RRAP). It provides a set of command-line tools to process environmental data, generate mortality scenarios, and package datasets for use in modeling frameworks like ADRIA.

## Key Features

- **Degree Heating Weeks (DHW):** Generate projected DHW datasets for specific reef clusters.
- **Cyclone Mortality:** Generate coral mortality datasets based on cyclone scenarios.
- **Domain Clustering:** Cluster reef locations for domain generation.
- **Initial Coral Cover:** Downscale and format initial coral cover data.
- **Data Store Integration:** Download datasets from the RRAP M&DS Data Store.
- **Standardized Packaging:** Tools to build and finalize ADRIA-compatible data packages.

## Project Structure

The project is structured into several specialized modules:

- `dhw`: Degree Heating Week projections.
- `cyclones`: Cyclone mortality modeling.
- `domain`: Spatial clustering of reef sites.
- `coral-cover`: Processing of initial coral cover.
- `data-store`: Interaction with the Provena-based Data Store.
- `template`: Automated building of domain data packages.
- `format`: Converters for various RME and CMIP6 data formats.
