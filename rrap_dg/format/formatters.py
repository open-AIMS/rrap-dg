import os
import glob
import pandas as pd
import geopandas as gpd
import juliacall
from typing import List, Dict, Tuple, Optional
from os.path import join as pj, basename

from rrap_dg import PKG_PATH
from .funcs import (
    format_connectivity_file, 
    reorder_location_perm, 
    format_single_rcp_dhw, 
    format_csv_dhw_model_group
)

# Initialize Julia module for ICC
jl_icc = juliacall.newmodule("DownscaleInitialCoralCover")
jl_icc.seval(f'include("{PKG_PATH}/initial_coral_cover/icc.jl")')

def _parse_timeframe(timeframe: str) -> Tuple[int, int]:
    try:
        parts = list(map(int, timeframe.split()))
        if len(parts) != 2:
            raise ValueError
        return (parts[0], parts[1])
    except ValueError:
        raise ValueError(f"Invalid timeframe format: '{timeframe}'. Expected 'YYYY YYYY'.")

def _find_rme_root(source_path: str) -> str:
    """Finds the root directory of a ReefMod Engine dataset."""
    if os.path.isdir(pj(source_path, "data_files")):
        return source_path

    if basename(source_path) == "data_files" and os.path.isdir(source_path):
        return os.path.dirname(source_path)

    found = glob.glob(pj(source_path, "**", "data_files"), recursive=True)
    found_dirs = [f for f in found if os.path.isdir(f)]

    if found_dirs:
        return os.path.dirname(found_dirs[0])

    raise FileNotFoundError("Unable to identify RME directory structure.")

def rme_connectivity(
    input_path: str,
    output_path: str,
    canonical_path: str,
    connectivity_pattern: str = "**/data_files/con_csv/CONNECT_ACRO*.csv",
    id_list_pattern: str = "**/data_files/id/id_list_*.csv"
) -> Tuple[str, str, str]:
    """
    Reformats all connectivity data found in the input path and saves to the output directory.
    Returns (resource_name, description, format).
    """
    connectivity_files = glob.glob(pj(input_path, connectivity_pattern), recursive=True)
    if not connectivity_files:
         raise RuntimeError(f"No connectivity CSVs found matching '{connectivity_pattern}' in {input_path}")

    rme_id_files = glob.glob(pj(input_path, id_list_pattern), recursive=True)
    if not rme_id_files:
        raise RuntimeError(f"No ID list found matching '{id_list_pattern}' in {input_path}")

    rme_ids = pd.read_csv(rme_id_files[0], comment="#", header=None)
    canonical = gpd.read_file(canonical_path)
    
    reorder_perm = reorder_location_perm(rme_ids[0], canonical.RME_GBRMPA_ID)

    os.makedirs(output_path, exist_ok=True)

    for con_fn in connectivity_files:
        fname = basename(con_fn)
        out_fn = pj(output_path, fname)
        print(f"  Formatting {fname} -> {out_fn}")
        con_df = format_connectivity_file(con_fn, reorder_perm, canonical["UNIQUE_ID"])
        con_df.to_csv(out_fn)

    return "connectivity", "Aligned RME connectivity matrices with canonical UNIQUE IDs.", "csv"

def standard_netcdf_dhw(
    input_path: str,
    output_path: str,
    rcps: str = "2.6 4.5 7.0 8.5",
    timeframe: str = "2025 2099",
    filename_template: str = "*{ssp}*"
) -> Tuple[str, str, str]:
    """
    Formats standard NetCDF DHW files.
    Returns (resource_name, description, format).
    """
    _timeframe = _parse_timeframe(timeframe)
    rcp_list = rcps.split()
    
    # Default map as per original implementation
    rcp_ssp_map = {
        "2.6": "ssp126",
        "4.5": "ssp245",
        "7.0": "ssp370",
        "8.5": "ssp585"
    }
    rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}

    format_rcps = []
    ssps = []
    for rcp in rcp_list:
        if rcp not in rcp_ssp_map:
             print(f"Warning: RCP {rcp} not found in map. Skipping.")
             continue
        format_rcps.append(rcps_fn.get(rcp, rcp.replace(".", "")))
        ssps.append(rcp_ssp_map[rcp])

    search_paths = [pj(input_path, filename_template.format(ssp=ssp)) for ssp in ssps]
    netcdf_files = [sorted(glob.glob(search_path)) for search_path in search_paths]

    os.makedirs(output_path, exist_ok=True)
    output_fps = [pj(output_path, f"dhwRCP{rcp}.nc") for rcp in format_rcps]

    for (src_files, out_fp) in zip(netcdf_files, output_fps):
        if not src_files:
            print(f"Warning: No source files found for RCP corresponding to {out_fp}")
            continue
        print(f"  Formatting to {out_fp}")
        format_single_rcp_dhw(src_files, out_fp, _timeframe)

    return "dhw", "Standardized NetCDF DHW files and aligned spatial coordinates.", "netcdf"

def rme_dhw(
    input_path: str,
    output_path: str,
    canonical_path: str,
    rcps: str = "2.6 4.5 7.0 8.5",
    timeframe: str = "2025 2099",
    dhw_csv_pattern: str = "**/data_files/dhw_csv/*.csv"
) -> Tuple[str, str, str]:
    """
    Formats RME DHW CSVs to NetCDF.
    Returns (resource_name, description, format).
    """
    _timeframe = _parse_timeframe(timeframe)
    rcp_list = rcps.split()
    
    canonical = gpd.read_file(canonical_path)
    canonical_ids = canonical["UNIQUE_ID"].tolist()

    rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}
    
    # Default match patterns
    rcp_match_patterns = {
        "2.6": ["126", "SSP126"],
        "4.5": ["245", "SSP245"],
        "7.0": ["370", "SSP370"],
        "8.5": ["585", "SSP585"]
    }

    os.makedirs(output_path, exist_ok=True)
    all_csvs = glob.glob(pj(input_path, dhw_csv_pattern), recursive=True)

    if not all_csvs:
        print(f"Warning: No CSV files found matching '{dhw_csv_pattern}' in {input_path}")

    for rcp in rcp_list:
        patterns = rcp_match_patterns.get(rcp, [])
        rcp_files = []
        for f in all_csvs:
            fname = basename(f)
            if any(pat in fname for pat in patterns):
                rcp_files.append(f)

        rcp_files = sorted(list(set(rcp_files)))

        if not rcp_files:
            print(f"Warning: No CSV files found for RCP {rcp}")
            continue

        out_fp = pj(output_path, f"dhwRCP{rcps_fn.get(rcp, rcp.replace('.', ''))}.nc")
        print(f"  Formatting RCP {rcp} ({len(rcp_files)} files) -> {out_fp}")

        format_csv_dhw_model_group(
            rcp_files,
            out_fp,
            _timeframe,
            canonical_ids
        )
    
    return "dhw", "Grouped DHW CSVs by RCP and converted to NetCDF, aligned with canonical IDs.", "netcdf"

def gbr_icc(
    input_path: str,
    output_path: str,
    canonical_path: str
) -> Tuple[str, str, str]:
    """
    Formats Initial Coral Cover (ICC) using Julia.
    Returns (resource_name, description, format).
    """
    rme_root_path = _find_rme_root(input_path)
    
    if not os.path.splitext(output_path)[1]:
        os.makedirs(output_path, exist_ok=True)
        out_file = pj(output_path, "coral_cover.nc")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        out_file = output_path

    print(f"  Formatting ICC from {rme_root_path} -> {out_file}")
    jl_icc.format_rme_icc(rme_root_path, canonical_path, out_file)

    return "coral_cover", "Processed RME Initial Coral Cover to NetCDF using spatial averaging.", "netcdf"