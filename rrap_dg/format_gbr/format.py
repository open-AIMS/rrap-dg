try:
    import tomllib
except ImportError:
    import tomli as tomllib

import typer
from .domain_builder import DomainBuilder

app = typer.Typer()

@app.command(help="Build an ADRIA Domain using a TOML configuration file.")
def build_domain(
    output_parent_dir: str = typer.Argument(..., help="The parent directory where the new domain folder will be created."),
    config_path: str = typer.Argument(..., help="Path to the TOML configuration file.")
) -> None:
    """
    Builds an ADRIA Domain dataset based on the provided TOML configuration.

    The configuration file defines:
    - Domain metadata
    - Data sources (handles or local paths)
    - Outputs to generate (connectivity, DHW, etc.) and the formatters to use.
    """
    builder = DomainBuilder(config_path, output_parent_dir)
    builder.build()
    print(f"Domain '{builder.config.domain_name}' built successfully at {builder.output_dir}")
