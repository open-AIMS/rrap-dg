import typer
import juliacall
from rrap_dg import PKG_PATH


jl = juliacall.newmodule("DomainClustering")
jl.seval(f'include("{PKG_PATH}/cluster_domain/domain_clustering.jl")')

app = typer.Typer()

@app.command(help="Create new geopackage file with clustered locations")
def cluster(
    gpkg_path: str,
    output_path: str,
) -> None:
    jl.cluster(gpkg_path, output_path)
