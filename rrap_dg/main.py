import typer
from rrap_dg import dhw
from rrap_dg import cyclones
from rrap_dg import cluster_domain

app = typer.Typer()
app.add_typer(dhw.app, name="dhw")
app.add_typer(cyclones.app, name="cyclones")
app.add_typer(cluster_domain.app, name="domain")


@app.callback()
def callback():
    """AIMS-RRAP Data Generator"""
