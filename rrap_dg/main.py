import typer
from rrap_dg import dhw

app = typer.Typer()
app.add_typer(dhw.app, name="dhw")


@app.callback()
def callback():
    """AIMS-RRAP Data Generator"""
