import typer
from rrap_dg import dhw
from rrap_dg import cyclones
from rrap_dg import cluster_domain
from rrap_dg import connectivity
from rrap_dg import initial_coral_cover

app = typer.Typer()
app.add_typer(dhw.app, name="dhw")
app.add_typer(cyclones.app, name="cyclones")
app.add_typer(cluster_domain.app, name="domain")
app.add_typer(initial_coral_cover.app, name="coral-cover")
app.add_typer(connectivity.app, name="connectivity")


@app.callback()
def callback():
    """AIMS-RRAP Data Generator"""
