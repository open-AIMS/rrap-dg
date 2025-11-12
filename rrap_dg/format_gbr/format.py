from .format_funcs import (
    format_connectivity_file, 
    format_single_rcp_dhw,
    reorder_location_perm, 
    format_connectivity_file
)

import geopandas as gpd
import pandas as pd

from os.path import join as pj
from os.path import basename
from glob  import glob
from rrap_dg import PKG_PATH

import typer
import juliacall

jl = juliacall.newmodule("DownscaleInitialCoralCover")
jl.seval(f'include("{PKG_PATH}/initial_coral_cover/icc.jl")')

app = typer.Typer()

@app.command(help="Format Degree Heating Week datasets.")
def format_dhw(
        source_dir: str,
        output_dir: str,
        rcps: str = typer.Option("2.6 4.5 7.0 8.5"),
        timeframe: str = typer.Option("2025 2099")
) -> None:
    _timeframe = tuple(map(int, timeframe.split(" ")))
    rcps_tuple = tuple(rcps.split(" "))
    rcps_to_ssps = {"2.6": "ssp126", "4.5": "ssp245", "7.0": "ssp370", "8.5": "ssp585"}
    rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}

    format_rcps = [rcps_fn[rcp] for rcp in rcps_tuple]
    ssps = [rcps_to_ssps[rcp] for rcp in rcps_tuple]
    search_paths = [pj(source_dir, f"*{ssp}*") for ssp in ssps]
    netcdf_files = [glob(search_path) for search_path in search_paths]
    output_fps = [pj(output_dir, f"dhwRCP{rcp}.nc") for rcp in format_rcps]

    for (src_files, out_fp) in zip(netcdf_files, output_fps):
        format_single_rcp_dhw(src_files, out_fp, _timeframe)

    return None

@app.command(help="Format ReefMod Engine connectivity datasets.")
def format_connectivity(
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

@app.command(help="Create initial coral cover netCDFs with custom bin edges for the entire GBR")
def format_icc(
    rme_path: str,
    canonical_path: str,
    output_path: str
):
    jl.format_rme_icc(rme_path, canonical_path, output_path)
    return None
