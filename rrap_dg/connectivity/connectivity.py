import typer

import pandas as pd
import geopandas as gpd
import numpy as np

from glob import glob
from os.path import join as pj
from os.path import basename

def reorder_location_perm(rme_order: list[str], canonical_order: list[str]) -> list[int]:
    rme_id_to_index = {id_val: i for i, id_val in enumerate(rme_order)}
    new_order_indices = [rme_id_to_index[id_val] for id_val in canonical_order]

    return new_order_indices

"""
    format_connectivity_file(filepath: str, reorder: list[int], unique_ids : list[str]) -> pd.Dataframe:

Add unique ids to columns and rows.
"""
def format_connectivity_file(
    filepath: str,
    reorder: list[int],
    unique_ids : list[str]
) -> pd.DataFrame:
    connectivity = pd.read_csv(filepath, header=None, comment='#')
    connectivity = connectivity.iloc[reorder, reorder]
    connectivity.index = unique_ids
    connectivity.columns = unique_ids

    return connectivity

app = typer.Typer()

@app.command(help="Format ReefMod Engine connectivity datasets.")
def format(
    rme_path: str,
    canonical_path: str,
    output_dir: str
) -> None:

    rme_data_path = pj(rme_path, "data_files")

    connectivity_path = pj(rme_data_path, "con_csv", "CONNECT_ACRO*.csv")
    connectivity_files = glob(connectivity_path)

    rme_id_list_path = pj(rme_data_path, "id", "id_list_*.csv")
    rme_id_file = glob(rme_id_list_path)[0]
    rme_ids = pd.read_csv(rme_id_file, comment="#", header=None)

    canonical = gpd.read_file(canonical_path)

    reorder_perm = reorder_location_perm(rme_ids[0], canonical.RME_GBRMPA_ID)
    output_paths = [pj(output_dir, basename(con_fn)) for con_fn in connectivity_files]

    for (con_fn, out_fn) in zip(connectivity_files, output_paths):
        con_df = format_connectivity_file(con_fn, reorder_perm, canonical["UNIQUE_ID"])
        con_df.to_csv(out_fn)

    return None
