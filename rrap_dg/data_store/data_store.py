from typing import Callable
from os.path import join as pj
from glob import glob

import numpy as np
import pandas as pd

import datapackage as dpkg
import boto3

# This is a helper function for managing authentication with Provena
import mdsisclienttools.auth.TokenManager as ProvenaAuth
import mdsisclienttools.datastore.ReadWriteHelper as ProvenaRW

import typer


# Provena Config
# Replace the domain with the domain of your Provena instance
PROVENA_DOMAIN = "mds.gbrrestoration.org"

app = typer.Typer()

@app.command(help="Download data from RRAP M&DS Data Store by handle id.")
def download(
    handle_id: str,
    dest: str
) -> None:
    """Download data from the RRAP M&DS data store using a handle id.

       Parameters
       ----------
       dest: str, output location of downloaded connectivity matrices
       handle_id: str, dataset id of the connectivity matrices
    """

    data_store_endpoint = "https://data-api.{}".format(PROVENA_DOMAIN)
    # Edit this to point to the Keycloak instance for your Provena instance
    kc_endpoint = "https://auth.mds.gbrrestoration.org/auth/realms/rrap"

    stage = "PROD"
    provena_auth = ProvenaAuth.DeviceFlowManager(
        stage=stage,
        keycloak_endpoint=kc_endpoint,
        auth_flow=ProvenaAuth.AuthFlow.DEVICE,
    )

    # expose the get auth function which is used for provena methods
    get_auth = provena_auth.get_auth
    ProvenaRW.download(data_store_api_endpoint=data_store_endpoint,handle=handle_id, auth=get_auth(), download_path=dest)
