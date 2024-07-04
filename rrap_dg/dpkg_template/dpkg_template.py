import os
from os.path import join as pj
from datetime import datetime

import typer


README_BASE = """
# ADRIA data package

Created: {created}


## Connectivity


## Cyclones


## DHWs


## Spatial


## Waves
"""


app = typer.Typer()

@app.command(help="Create empty ADRIA Domain data package")
def generate(template_path: str):
    os.makedirs(pj(template_path, "connectivity"))
    os.makedirs(pj(template_path, "cyclones"))
    os.makedirs(pj(template_path, "DHWs"))
    os.makedirs(pj(template_path, "spatial"))
    os.makedirs(pj(template_path, "waves"))
    open(pj(template_path, "datapackage.json"), "a").close()

    with open(pj(template_path, "README.md"), "a") as fp:
        fp.write(README_BASE.format(created=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

@app.command(help="Create ADRIA Domain data package pre-filling with data from data store")
def package(template_path: str, spec: str):
    print("Not yet implemented")

    # generate(template_path)
    # TODO: download datasets defined in a spec file to appropriate sub-directories
