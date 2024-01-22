import typer
import juliacall


jl = juliacall.newmodule("DomainClustering")
jl.seval('include("rrap_dg/cluster_domain/domain_clustering.jl")')

app = typer.Typer()

@app.command(help="Create new geopackage file with clustered locations")
def cluster(
    gpkg_path: str,
    output_path: str,
) -> None:
    jl.cluster(gpkg_path, output_path)
