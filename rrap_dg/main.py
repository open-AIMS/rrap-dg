import typer
from rrap_dg import dhw
from rrap_dg import cyclones

app = typer.Typer()
app.add_typer(dhw.app, name="dhw")
app.add_typer(cyclones.app, name="cyclones")


@app.callback()
def callback():
    """AIMS-RRAP Data Generator"""
