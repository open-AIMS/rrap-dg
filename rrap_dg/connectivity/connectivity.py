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


def download(dest: str, dataset_id: str, get_auth: Callable):
    data_store_endpoint = "https://data-api.{}".format(PROVENA_DOMAIN)
    ProvenaRW.download(data_store_api_endpoint=data_store_endpoint,handle=dataset_id, auth=get_auth(), download_path=dest)


# Edit this to point to the Keycloak instance for your Provena instance
kc_endpoint = "https://auth.mds.gbrrestoration.org/auth/realms/rrap"

# app = typer.Typer()

stage = "PROD"
provena_auth = ProvenaAuth.DeviceFlowManager(
    stage=stage,
    keycloak_endpoint=kc_endpoint,
    auth_flow=ProvenaAuth.AuthFlow.DEVICE,
)

# expose the get auth function which is used for provena methods
get_auth = provena_auth.get_auth

# some handle id - This one is Lizard Island connectivity with mortality
ds_id = "102.100.100/602432"
download(".", ds_id, get_auth)  # download to current folder
