import typer
from rrap_dg import dhw
from rrap_dg import connectivity
from rrap_dg import cyclones
from rrap_dg import cluster_domain
from rrap_dg import data_store
from rrap_dg import initial_coral_cover
from rrap_dg import dpkg_template

app = typer.Typer()
app.add_typer(dhw.app, name="dhw")
app.add_typer(connectivity.app, name="connectivity")
app.add_typer(cyclones.app, name="cyclones")
app.add_typer(cluster_domain.app, name="domain")
app.add_typer(initial_coral_cover.app, name="coral-cover")
app.add_typer(data_store.app, name="data-store")
app.add_typer(dpkg_template.app, name="template")


@app.callback()
def callback():
    """AIMS-RRAP Data Generator"""
