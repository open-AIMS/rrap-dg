import typer
import juliacall
from rrap_dg import PKG_PATH


jl = juliacall.newmodule("Cyclones")
jl.seval(f'include("{PKG_PATH}/cyclones/datacube_generator.jl")')

app = typer.Typer()

@app.command(help="Generate Cyclones mortality datasets")
def generate(
    rrapdg_datapackage_path: str,
    rme_datapackage_path: str,
    output_path: str,
    cluster_name: str = typer.Option(None, help="Explicit name of the cluster."),
) -> None:
    jl.generate(
        rrapdg_datapackage_path,
        rme_datapackage_path,
        output_path,
        cluster_name=cluster_name,
    )