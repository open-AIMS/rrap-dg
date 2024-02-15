import typer
import juliacall


jl = juliacall.newmodule("DownscaleInitialCoralCover")
jl.seval('include("rrap_dg/initial_coral_cover/icc.jl")')

app = typer.Typer()

@app.command(help="Create new netCDF with initial coral cover values.")
def downscale_icc(
    rrapdg_dpkg_path: str,
    target_cluster: str,
    output_path: str,
) -> None:
    jl.downscale_icc(rrapdg_dpkg_path, target_cluster, output_path)
