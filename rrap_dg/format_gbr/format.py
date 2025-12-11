from .format_funcs import (
    format_connectivity_file,
    format_single_rcp_dhw,
    reorder_location_perm,
    format_connectivity_file
)

import os
import json
import geopandas as gpd
import pandas as pd
from string import Template
from itertools import groupby

from os.path import join as pj
from os.path import basename, exists
from glob  import glob
import tempfile
from typing import Optional
from datetime import datetime
from rrap_dg import PKG_PATH, DATAPACKAGE_VERSION
from rrap_dg.dpkg_template.dpkg_template import generate as generate_dpkg
from rrap_dg.data_store.data_store import download as download_data

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import typer
import juliacall

jl = juliacall.newmodule("DownscaleInitialCoralCover")
jl.seval(f'include("{PKG_PATH}/initial_coral_cover/icc.jl")')

app = typer.Typer()

def _update_datapackage(
    output_dir: str,
    canonical_meta_path: Optional[str],
    dhw_meta_path: Optional[str],
    rme_meta_path: Optional[str],
    timeframe: str,
    location_id_col: str,
    cluster_id_col: str,
    k_col: str,
    area_col: str,
    canonical_handle: Optional[str] = None,
    dhw_handle: Optional[str] = None,
    rme_handle: Optional[str] = None,
    waves_path: str = "",
    waves_desc: str = "No data provided/available.",
    cyclones_path: str = "",
    cyclones_desc: str = "No data provided/available."
):
    dpkg_path = pj(output_dir, "datapackage.json")
    if not exists(dpkg_path):
        return

    domain_name = basename(output_dir)
    
    # Calculate dynamic values for template
    timeframe_list_str = str(list(map(int, timeframe.split(" "))))
    
    num_locations_val = "null" # Default to null if GeoPackage not found or read fails
    gpkg_path = pj(output_dir, "spatial", f"{domain_name}.gpkg")
    if exists(gpkg_path):
        try:
            gdf = gpd.read_file(gpkg_path)
            num_locations_val = str(len(gdf)) # Convert to string for template
        except Exception as e:
            print(f"Warning: Could not read geopackage at {gpkg_path} to determine num_locations. Error: {e}")

    dhw_desc_val = "Degree heating week data." if dhw_meta_path else "No data provided/available."
    dhw_path_val = "DHWs" if dhw_meta_path else ""

    # Read and format the template
    template_path = pj(PKG_PATH, "format_gbr", "datapackage.json.template")
    with open(template_path, "r") as f:
        template_content = f.read()

    template = Template(template_content)
    formatted_template = template.substitute(
        domain_name=domain_name,
        domain_title=f"{domain_name} Domain",
        version=DATAPACKAGE_VERSION,
        timeframe_list=timeframe_list_str,
        num_locations=num_locations_val,
        location_id_col=location_id_col,
        cluster_id_col=cluster_id_col,
        k_col=k_col,
        area_col=area_col,
        dhw_desc=dhw_desc_val,
        dhw_path=dhw_path_val,
        waves_desc=waves_desc,
        waves_path=waves_path,
        cyclones_desc=cyclones_desc,
        cyclones_path=cyclones_path
    )
    dpkg = json.loads(formatted_template)

    meta_files = {
        "Canonical": canonical_meta_path,
        "DHW": dhw_meta_path,
        "RME": rme_meta_path
    }
    
    source_handles = {
        "Canonical": canonical_handle,
        "DHW": dhw_handle,
        "RME": rme_handle
    }

    contributors = {}

    for source_name, meta_path in meta_files.items():
        if meta_path and exists(meta_path):
            with open(meta_path, "r") as f:
                try:
                    meta = json.load(f)
                    dataset_info = meta.get("dataset_info", {})
                    
                    # Add as source
                    dpkg["sources"].append({
                        "title": dataset_info.get("name", f"{source_name} Dataset"),
                        "description": dataset_info.get("description", ""),
                        "path": "",
                        "handle": source_handles.get(source_name, "") or ""
                    })

                    # Extract contributor/contact
                    associations = meta.get("associations", {})
                    contact = associations.get("point_of_contact")
                    data_custodian_id = associations.get("data_custodian_id")
                    
                    if contact:
                        if contact not in contributors:
                            contributors[contact] = {
                                "title": contact.split("@")[0], # Fallback name
                                "email": contact,
                                "role": "author",
                                "description": f"Point of contact for {source_name} dataset"
                            }
                        else:
                            contributors[contact]["description"] += f", {source_name}"
                        
                        if data_custodian_id:
                            contributors[contact]["data_custodian_id"] = data_custodian_id
                    
                    # Maybe append rights holder to contributors or separate field?
                    rights_holder = dataset_info.get("rights_holder")
                    if rights_holder:
                         # Check if already added?
                         pass

                except json.JSONDecodeError:
                    print(f"Warning: Could not decode metadata file at {meta_path}")

    dpkg["contributors"] = list(contributors.values())

    with open(dpkg_path, "w") as f:
        json.dump(dpkg, f, indent=4)


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
    netcdf_files = [sorted(glob(search_path)) for search_path in search_paths]
    output_fps = [pj(output_dir, f"dhwRCP{rcp}.nc") for rcp in format_rcps]

    for (src_files, out_fp) in zip(netcdf_files, output_fps):
        format_single_rcp_dhw(src_files, out_fp, _timeframe)

    # Update README with GCM info
    readme_path = pj(os.path.dirname(output_dir), "README.md")
    if exists(readme_path) and netcdf_files and netcdf_files[0]:
        # Assuming all RCPs have the same GCMs in the same order
        # Use the first RCP list to extract GCMs
        first_rcp_files = netcdf_files[0]
        gcms_list = []
        for fp in first_rcp_files:
            filename = basename(fp)
            # Expected format: CoralSea_GBR_GCMNAME_...
            parts = filename.split("_")
            if len(parts) > 2:
                gcms_list.append(parts[2])
            else:
                gcms_list.append("Unknown")
        
        # Group and calculate ranges (files are sorted, so identical GCMs are adjacent)
        grouped_gcms = [(key, len(list(group))) for key, group in groupby(gcms_list)]

        with open(readme_path, "a") as f:
            f.write("\n\n## DHW Climate Models\n\n")
            f.write("The `model` dimension in the DHW NetCDF files corresponds to the following climate models (indices are 1-based):\n\n")
            
            current_idx = 1
            for gcm, count in grouped_gcms:
                end_idx = current_idx + count - 1
                if count > 1:
                    f.write(f"*   {gcm} ({current_idx}:{end_idx})\n")
                else:
                    f.write(f"*   {gcm} ({current_idx})\n")
                current_idx += count

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



def _write_domain_readme(output_dir: str, domain_name: str, version: str, spatial_cols: dict):
    readme_path = pj(output_dir, "README.md")
    template_path = pj(PKG_PATH, "format_gbr", "domain_readme.md.template")
    
    with open(template_path, "r") as f:
        template = f.read()
    
    date_str = datetime.today().strftime('%Y-%m-%d')
    
    content = template.format(
        domain_name=domain_name,
        date_str=date_str,
        version=version,
        location_id_col=spatial_cols.get('location_id_col', 'UNIQUE_ID'),
        area_col=spatial_cols.get('area_col', 'ReefMod_area_m2'),
        k_col=spatial_cols.get('k_col', 'ReefMod_habitable_proportion'),
        cluster_id_col=spatial_cols.get('cluster_id_col', 'UNIQUE_ID')
    )
    
    with open(readme_path, "w") as f:
        f.write(content)

@app.command(help="Generate a GBR-wide ADRIA Domain from local files.")
def generate_domain_from_local(
    output_dir: str,
    canonical_gpkg: str,
    dhw_path: str,
    rme_path: str,
    rcps: str = typer.Option("2.6 4.5 7.0 8.5"),
    timeframe: str = typer.Option("2025 2099"),
    location_id_col: str = typer.Option("UNIQUE_ID"),
    cluster_id_col: str = typer.Option("UNIQUE_ID"),
    k_col: str = typer.Option("ReefMod_habitable_proportion"),
    area_col: str = typer.Option("ReefMod_area_m2")
):
    generate_dpkg(output_dir)
    
    # Overwrite README with custom GBR template
    spatial_cols = {
        "location_id_col": location_id_col,
        "cluster_id_col": cluster_id_col,
        "k_col": k_col,
        "area_col": area_col
    }
    _write_domain_readme(output_dir, basename(output_dir), DATAPACKAGE_VERSION.replace(".", ""), spatial_cols)

    format_dhw(dhw_path, pj(output_dir, "DHWs"), rcps, timeframe)
    format_connectivity(rme_path, canonical_gpkg, pj(output_dir, "connectivity"))
    format_icc(rme_path, canonical_gpkg, pj(output_dir, "spatial", "coral_cover.nc"))

    gdf = gpd.read_file(canonical_gpkg)
    gdf["cluster_id"] = range(1, len(gdf) + 1)
    gdf.to_file(pj(output_dir, "spatial", f"{basename(output_dir)}.gpkg"), driver="GPKG")

    return None

@app.command(help="Generate a GBR-wide ADRIA Domain from Data Store Handles or local paths.")
def generate_domain_from_store(
    output_parent_dir: str = typer.Argument(..., help="Parent directory where the domain will be saved"),
    domain_name: str = typer.Argument(..., help="Name of the domain (e.g., GBR)"),
    config: str = typer.Option(..., "--config", "-c", help="Path to TOML configuration file.")
):

    with open(config, "rb") as f:
        cfg = tomllib.load(f)

    spatial_cfg = cfg.get("spatial", {})

    canonical_gpkg_handle = spatial_cfg.get("handle")
    canonical_gpkg_path = spatial_cfg.get("path")

    dhw_handle = cfg.get("dhw", {}).get("handle")
    dhw_path = cfg.get("dhw", {}).get("path")

    rme_handle = cfg.get("rme", {}).get("handle")
    rme_path = cfg.get("rme", {}).get("path")

    rcps = cfg.get("options", {}).get("rcps", "2.6 4.5 7.0 8.5")
    timeframe = cfg.get("options", {}).get("timeframe", "2025 2099")
    
    location_id_col = spatial_cfg.get("location_id_col", "UNIQUE_ID")
    cluster_id_col = spatial_cfg.get("cluster_id_col", "UNIQUE_ID")
    k_col = spatial_cfg.get("k_col", "ReefMod_habitable_proportion")
    area_col = spatial_cfg.get("area_col", "ReefMod_area_m2")

    # Waves and Cyclones
    waves_cfg = cfg.get("waves", {})
    waves_path = waves_cfg.get("path", "")
    waves_desc = waves_cfg.get("description", "No data provided/available.")

    cyclones_cfg = cfg.get("cyclones", {})
    cyclones_path = cyclones_cfg.get("path", "")
    cyclones_desc = cyclones_cfg.get("description", "No data provided/available.")
    
    # Construct output directory path
    date_str = datetime.today().strftime('%Y-%m-%d')
    version_str = DATAPACKAGE_VERSION.replace(".", "")
    output_dir_name = f"{domain_name}_{date_str}_v{version_str}"
    output_dir = pj(output_parent_dir, output_dir_name)

    if os.path.exists(output_dir):
        raise typer.BadParameter(f"Output directory '{output_dir}' already exists. Please specify a new directory or remove the existing one.")


    with tempfile.TemporaryDirectory() as tmp_dir:
        # Resolve canonical geopackage source
        canonical_gpkg_resolved_path: str = ""
        canonical_meta_path: Optional[str] = None
        if canonical_gpkg_handle and canonical_gpkg_path:
            raise typer.BadParameter("Cannot specify both 'handle' and 'path' for canonical geopackage under [spatial] in configuration.")
        elif canonical_gpkg_handle:
            canonical_dir = pj(tmp_dir, "canonical")
            print(f"Downloading canonical geopackage (handle: {canonical_gpkg_handle})...")
            download_data(canonical_gpkg_handle, canonical_dir)
            gpkg_files = glob(pj(canonical_dir, "*.gpkg"))
            if not gpkg_files:
                raise RuntimeError(f"No .gpkg file found in downloaded canonical dataset from handle {canonical_gpkg_handle}")
            canonical_gpkg_resolved_path = gpkg_files[0]
            canonical_meta_path = pj(canonical_dir, "metadata.json")
        elif canonical_gpkg_path:
            canonical_gpkg_resolved_path = canonical_gpkg_path
        else:
            raise typer.BadParameter("Either 'handle' or 'path' must be specified for the canonical geopackage under [spatial] in configuration.")

        # Resolve DHW source
        dhw_resolved_path: str = ""
        dhw_meta_path: Optional[str] = None
        if dhw_handle and dhw_path:
            raise typer.BadParameter("Cannot specify both handle and path for DHW dataset in configuration.")
        elif dhw_handle:
            dhw_dir = pj(tmp_dir, "dhw")
            print(f"Downloading DHW dataset (handle: {dhw_handle})...")
            download_data(dhw_handle, dhw_dir)
            dhw_resolved_path = dhw_dir
            dhw_meta_path = pj(dhw_dir, "metadata.json")
        elif dhw_path:
            dhw_resolved_path = dhw_path
        else:
            raise typer.BadParameter("Either handle or path must be specified for the DHW dataset in configuration.")

        # Resolve RME source
        rme_resolved_path: str = ""
        rme_meta_path: Optional[str] = None
        if rme_handle and rme_path:
            raise typer.BadParameter("Cannot specify both handle and path for ReefMod Engine dataset in configuration.")
        elif rme_handle:
            rme_dir = pj(tmp_dir, "rme")
            print(f"Downloading ReefMod Engine dataset (handle: {rme_handle})...")
            download_data(rme_handle, rme_dir)
            rme_meta_path = pj(rme_dir, "metadata.json")

            # Search for 'data_files' directory
            data_files_search = glob(pj(rme_dir, "**", "data_files"), recursive=True)
            if not data_files_search:
                 raise RuntimeError(f"No 'data_files' directory found in downloaded RME dataset from handle {rme_handle}")
            
            # The RME path expected by downstream functions is the directory containing 'data_files'
            rme_resolved_path = os.path.dirname(data_files_search[0])
        elif rme_path:
            rme_resolved_path = rme_path
        else:
            raise typer.BadParameter("Either handle or path must be specified for the ReefMod Engine dataset in configuration.")

        print("Formatting domain...")
        generate_domain_from_local(output_dir, canonical_gpkg_resolved_path, dhw_resolved_path, rme_resolved_path, rcps, timeframe, location_id_col, cluster_id_col, k_col, area_col)

        _update_datapackage(
            output_dir, 
            canonical_meta_path, 
            dhw_meta_path, 
            rme_meta_path, 
            timeframe,
            location_id_col,
            cluster_id_col,
            k_col,
            area_col,
            canonical_handle=canonical_gpkg_handle,
            dhw_handle=dhw_handle,
            rme_handle=rme_handle,
            waves_path=waves_path,
            waves_desc=waves_desc,
            cyclones_path=cyclones_path,
            cyclones_desc=cyclones_desc
        )
    
    return None

