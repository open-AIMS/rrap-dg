import typer
import juliacall

jl = juliacall.newmodule("Cyclones")

jl.seval('include("rrap_dg/cyclones/datacube_generator.jl")')

app = typer.Typer()

@app.command(help="Generate Cyclones mortality datasets")
def generate(
    rrapdg_datapackage_path: str,
    rme_datapackage_path: str,
    output_path: str,
    #gen_year: str = typer.Option("2025 2100"),
) -> None:
    jl.generate(rrapdg_datapackage_path, rme_datapackage_path, output_path)