import typer
import juliacall

jl = juliacall.newmodule("Cyclones")

jl.seval('include("rrap_dg/cyclones/cyclones.jl")')

app = typer.Typer()

@app.command(help="Generate Cyclone mortality datasets")
def generate(
    input_path: str,
    gen_year: str = typer.Option("2025 2100"),
) -> None:
    y_b3, y_b8, y_m = jl.cyclone_mortality(input_path)

    print(y_b3(25))
