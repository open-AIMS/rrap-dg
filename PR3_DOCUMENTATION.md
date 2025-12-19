# PR 3: Documentation & Workflows

## Description
This PR completes the feature delivery by adding comprehensive documentation for the new CLI tools and setting up automated documentation deployment.

## Key Changes
- **User Documentation:**
  - `docs/gbr_domain.md`: Detailed guide on using the GBR Domain Generator, including configuration structure and available formatters.
  - `docs/cli.md`: Reference for the CLI commands.
  - `docs/data_store.md`: Guide for interacting with the Data Store.
  - `docs/installation.md`: Updated installation instructions.
- **Project Documentation:**
  - Updated `README.md` to reflect the new capabilities.
  - Updated `mkdocs.yml` navigation structure.
- **CI/CD:**
  - Added `.github/workflows/deploy_docs.yml` to automate the deployment of MkDocs to GitHub Pages.

## Motivation
To ensure adoption and usability, clear documentation is essential. The automated workflow ensures that the documentation site remains up-to-date with the codebase.

## Dependencies
- Depends on PR #2 (`feature/domain-logic`).
