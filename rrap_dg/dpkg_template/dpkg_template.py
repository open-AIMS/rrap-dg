import os
import re
import shutil
import tomllib
from os.path import join as pj
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from asyncio import run

import typer

from rrap_dg.__about__ import DATAPACKAGE_VERSION
from rrap_dg.data_store.data_store import (
    download,
    download_specific_file_async,
    list_all_files_async,
)
from rrap_dg.utils import is_handle_id
from rrap_dg.dpkg_template.packaging import finalize_domain_package

app = typer.Typer()

def _fetch_datastore_metadata(
    handle_id: str,
    dest_dir: str,
    resource_name: str
):
    metadata_filenames = ["datapackage.json", "metadata.json", "ro-crate-metadata.json"]
    dst_fn = os.path.join(dest_dir, f"{resource_name}.metadata.json")
    available_files = run(list_all_files_async(handle_id))
    for mf in metadata_filenames:
        if any(f.endswith(mf) for f in available_files):
            # Find the actual path if it's nested
            match = next((f for f in available_files if f.endswith(mf)), None)
            if match:
                # Download to the destination directory
                run(download_specific_file_async(handle_id, match, dest_dir))
                
                # The file will be named according to its basename in S3
                downloaded_file = os.path.join(dest_dir, os.path.basename(match))
                if os.path.exists(downloaded_file):
                    # Rename it to our internal metadata name
                    os.rename(downloaded_file, dst_fn)
                return None

    print(f"Unable to locate metadata file from {handle_id}. Check the handle id \
            contain one of the following {metadata_filenames}")

def _fetch_local_metadata(
    source: str,
    dest_dir: str,
    resource_name: str
):
    metadata_filenames = ["datapackage.json", "metadata.json", "ro-crate-metadata.json"]
    dst_fn = os.path.join(dest_dir, f"{resource_name}.metadata.json")

    # Retrieve metadata from local source.
    if not os.path.isdir(source):
        print(f"Unable to locate metadata for {source}. If metadata is contained in the \
            parent directory, pass the parent directory as source and name the specific \
            file to use as an option.")

    for mf in metadata_filenames:
        src_f = os.path.join(source, mf)
        if os.path.exists(src_f):
            shutil.copy2(src_f, dst_fn)
            return None

    return None

def _fetch_metadata(
    source: str,
    dest_dir: str,
    resource_name: str,
):
    if is_handle_id(source):
        _fetch_datastore_metadata(source, dest_dir, resource_name)
        return None

    if os.path.exists(source):
        _fetch_local_metadata(source, dest_dir, resource_name)
        return None

    raise ValueError(f"Source must be a handle id or path. Given source was {source}.")

def _fetch_local_dataset(
    source: str,
    dest_dir: str,
    specific_files: Optional[List[str]] = None
) -> None:
    os.makedirs(dest_dir, exist_ok=True)

    if not os.path.isdir(source):
        shutil.copy2(source, dest_dir)
        return None

    if specific_files is None:
        shutil.copytree(source, dest_dir, dirs_exist_ok=True)
        return None

    for f in specific_files:
        src_f = os.path.join(source, f)
        dest_f = os.path.join(dest_dir, os.path.basename(f))
        shutil.copy2(src_f, dest_f)

    return None


def _fetch_datastore_dataset(
    source: str,
    dest_dir: str,
    specific_files: Optional[List[str]] = None
):
    print(f"Fetching handle ID: {source} -> {dest_dir}")
    try:
        if specific_files:
            # List files to verify and include metadata
            available_files = run(list_all_files_async(source))
            to_download = set(specific_files)

            for f in to_download:
                if f in available_files:
                    run(download_specific_file_async(source, f, dest_dir))
                else:
                    print(f"Warning: File {f} not found in handle {source}")
        else:
            download(source, dest_dir)
    except Exception as e:
        print(f"Error fetching handle {source}: {e}")
        raise typer.Exit(code=1)

    return None

def fetch_dataset(
    source: str,
    dest_dir: str,
    resource_name: str,
    specific_files: Optional[List[str]] = None,
):
    if is_handle_id(source):
        _fetch_datastore_dataset(source, dest_dir, specific_files)
    elif os.path.exists(source):
        _fetch_local_dataset(source, dest_dir, specific_files)
    else:
        raise ValueError(f"Source must be a handle id or path. Given source was {source}.")

    # Remove duplicated metadata from the destination to keep it clean
    for mf in ["datapackage.json", "metadata.json", "ro-crate-metadata.json"]:
        target = os.path.join(dest_dir, mf)
        if os.path.exists(target):
            os.remove(target)

    _fetch_metadata(source, dest_dir, resource_name)

    return source

def create_domain_dir_name(base_name: str):
    """Create the standard domain directory name, including versioning and date."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    version_tag = f"v{DATAPACKAGE_VERSION.replace('.', '')}"
    return f"{base_name}_{today_str}_{version_tag}"

def get_source_and_files(config, key):
    source = None
    files = None
    if key in config:
        source = config[key].get("source", None)
        files = config[key].get("files", None)
    return source, files

@app.command(help="Create empty ADRIA Domain data package")
def generate(template_path: str):
    if os.path.exists(template_path):
        raise FileExistsError(f"Directory already exists: {template_path}")

    os.makedirs(pj(template_path, "connectivity"))
    os.makedirs(pj(template_path, "cyclones"))
    os.makedirs(pj(template_path, "DHWs"))
    os.makedirs(pj(template_path, "spatial"))
    os.makedirs(pj(template_path, "waves"))

    # Initialize empty files
    with open(pj(template_path, "datapackage.json"), "w") as f:
        pass
    with open(pj(template_path, "README.md"), "w") as f:
        pass

@app.command(help="Build ADRIA Domain by fetching datasets into a standardized structure.")
def build(
    config_path: str = typer.Argument(..., help="Path to a TOML configuration file."),
    output_path: str = typer.Argument(..., help="Path to create the domain directory."),
):
    """
    Builds an ADRIA Domain by downloading (from data store) or copying (from local path) datasets.
    Sources and file lists are configured via a TOML config file.
    """
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Get general configuration
    domain_name = config.get("domain_name", "GBR")

    # Get sources and file lists
    spatial_source, spatial_files = get_source_and_files(config, "spatial")
    dhw_source, dhw_files = get_source_and_files(config, "dhw")
    connectivity_source, connectivity_files = get_source_and_files(config, "connectivity")
    icc_source, icc_files = get_source_and_files(config, "icc")
    cyclones_source, cyclones_files = get_source_and_files(config, "cyclones")
    waves_source, waves_files = get_source_and_files(config, "waves")

    # Validate required sources
    required = {
        "spatial_source": spatial_source,
        "dhw_source": dhw_source,
        "connectivity_source": connectivity_source,
        "icc_source": icc_source,
    }
    for name, val in required.items():
        if val is None:
            typer.secho(f"Error: {name} is required in config.", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    # Construct the final output directory name
    domain_dir_name = create_domain_dir_name(domain_name)
    final_output_path = os.path.join(output_path, domain_dir_name)

    print(f"Building domain at {final_output_path}...")

    try:
        generate(final_output_path)
    except FileExistsError as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)

    # Fetch Required Datasets
    print("Fetching Spatial data...")
    spatial_dest = pj(final_output_path, "spatial")
    fetch_dataset(spatial_source, spatial_dest, resource_name="spatial", specific_files=spatial_files)

    # Rename the spatial geopackage to match the domain name and version
    gpkgs = list(Path(spatial_dest).glob("*.gpkg"))
    if gpkgs:
        # Assuming the first .gpkg is the primary spatial geometry
        old_gpkg = gpkgs[0]
        new_gpkg = Path(spatial_dest) / f"{domain_dir_name}.gpkg"
        if old_gpkg.name != new_gpkg.name:
            print(f"Renaming {old_gpkg.name} -> {new_gpkg.name}")
            old_gpkg.rename(new_gpkg)

    print("Fetching DHW data...")
    fetch_dataset(dhw_source, pj(final_output_path, "DHWs"), resource_name="dhw", specific_files=dhw_files)

    print("Fetching Connectivity data...")
    fetch_dataset(connectivity_source, pj(final_output_path, "connectivity"), resource_name="connectivity", specific_files=connectivity_files)

    print("Fetching Initial Coral Cover data...")
    fetch_dataset(icc_source, pj(final_output_path, "spatial"), resource_name="icc", specific_files=icc_files)

    # Rename the ICC NetCDF to coral_cover.nc
    icc_ncs = list(Path(spatial_dest).glob("*.nc"))
    if icc_ncs:
        # Assuming the first .nc is the ICC
        old_icc = icc_ncs[0]
        new_icc = Path(spatial_dest) / "coral_cover.nc"
        if old_icc.name != new_icc.name:
            print(f"Renaming {old_icc.name} -> {new_icc.name}")
            old_icc.rename(new_icc)

    # Fetch Optional Datasets
    if cyclones_source:
        print("Fetching Cyclones data...")
        fetch_dataset(cyclones_source, pj(final_output_path, "cyclones"), resource_name="cyclones", specific_files=cyclones_files)

    if waves_source:
        print("Fetching Waves data...")
        fetch_dataset(waves_source, pj(final_output_path, "waves"), resource_name="waves", specific_files=waves_files)

    print("Directory structure created and datasets fetched.")

    print("Finalizing datapackage.json...")
    finalize_domain_package(
        domain_path=Path(final_output_path),
        domain_name=domain_name,
        spatial_source=spatial_source,
        dhw_source=dhw_source,
        connectivity_source=connectivity_source,
        icc_source=icc_source,
        cyclones_source=cyclones_source,
        waves_source=waves_source
    )

    # Post-build cleanup: remove temporary metadata files
    for root, _, files in os.walk(final_output_path):
        for f in files:
            if f.endswith(".metadata.json"):
                os.remove(os.path.join(root, f))

    typer.secho("\nDomain built successfully.", fg=typer.colors.GREEN, bold=True)
    typer.echo("Note: You must manually update the generated 'datapackage.json' to specify")
    typer.echo("      column names for the spatial resource (location_id_col, cluster_id_col,")
    typer.echo("      k_col, and area_col) to ensure compatibility with ADRIA.")
    typer.echo("      You should also create a README.md to describe the domain.")


