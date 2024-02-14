import typer
import juliacall


jl = juliacall.newmodule("DownscaleInitialCoralCover")
jl.seval('include("rrap_dg/initial_coral_cover/icc.jl")')

app = typer.Typer()

@app.command(help="Create new netCDF with initial coral cover values.")
def downscale_icc(
    rme_path: str,
    target_gpkg: str,
    output_path: str,
) -> None:
    jl.downscale_icc(rme_path, target_gpkg, output_path)
