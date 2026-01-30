import os
import shutil
from os.path import join as pj
from datetime import datetime
from typing import Optional
from pathlib import Path

import typer

from rrap_dg.data_store.data_store import download
from rrap_dg.dpkg_template.packaging import finalize_domain_package

app = typer.Typer()

def fetch_dataset(source: str, dest_dir: str, rename_metadata_to: Optional[str] = None):
    """Fetches a dataset from a local path or a handle ID and optionally renames metadata."""
    if os.path.exists(source):
        print(f"Copying from local path: {source} -> {dest_dir}")
        if os.path.isdir(source):
            for item in os.listdir(source):
                s = os.path.join(source, item)
                d = os.path.join(dest_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        else:
            # If source is a file, copy it into dest_dir
            shutil.copy2(source, dest_dir)
    else:
        # Assume it's a handle ID
        print(f"Fetching handle ID: {source} -> {dest_dir}")
        try:
            download(source, dest_dir)
        except Exception as e:
            print(f"Error fetching handle {source}: {e}")
            raise typer.Exit(code=1)

    # Rename metadata if requested
    if rename_metadata_to:
        potential_files = ["datapackage.json", "metadata.json", "ro-crate-metadata.json"]
        renamed = False
        for mf in potential_files:
            p = os.path.join(dest_dir, mf)
            if os.path.exists(p):
                new_path = os.path.join(dest_dir, rename_metadata_to)
                print(f"Renaming {mf} -> {rename_metadata_to}")
                shutil.move(p, new_path)
                renamed = True
                break
        if not renamed:
            print(f"Warning: Could not find metadata file to rename to {rename_metadata_to} in {dest_dir}")

    return source

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
    output_path: str = typer.Argument(..., help="Path to create the domain directory."),
    spatial_source: str = typer.Option(..., help="Source (Handle ID or local path) for Spatial data (GeoPackage)."),
    dhw_source: str = typer.Option(..., help="Source (Handle ID or local path) for DHW data (NetCDFs)."),
    connectivity_source: str = typer.Option(..., help="Source (Handle ID or local path) for Connectivity data (CSVs)."),
    icc_source: str = typer.Option(..., help="Source (Handle ID or local path) for Initial Coral Cover data (NetCDF)."),
    cyclones_source: Optional[str] = typer.Option(None, help="Optional: Source (Handle ID or local path) for Cyclones data."),
    waves_source: Optional[str] = typer.Option(None, help="Optional: Source (Handle ID or local path) for Waves data."),
    domain_name: str = typer.Option("GBR", help="Name for the generated Domain Datapackage.")
):
    """
    Builds an ADRIA Domain by downloading (from data store) or copying (from local path) datasets.
    """
    print(f"Building domain at {output_path}...")

    try:
        generate(output_path)
    except FileExistsError as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)

    # Fetch Required Datasets
    print("Fetching Spatial data...")
    fetch_dataset(spatial_source, pj(output_path, "spatial"), rename_metadata_to="spatial_metadata.json")

    print("Fetching DHW data...")
    fetch_dataset(dhw_source, pj(output_path, "DHWs"), rename_metadata_to="dhw_datapackage.json")

    print("Fetching Connectivity data...")
    fetch_dataset(connectivity_source, pj(output_path, "connectivity"), rename_metadata_to="connectivity_datapackage.json")

    print("Fetching Initial Coral Cover data...")
    fetch_dataset(icc_source, pj(output_path, "spatial"), rename_metadata_to="icc_datapackage.json")

    # Fetch Optional Datasets
    if cyclones_source:
        print("Fetching Cyclones data...")
        fetch_dataset(cyclones_source, pj(output_path, "cyclones"), rename_metadata_to="cyclones_datapackage.json")

    if waves_source:
        print("Fetching Waves data...")
        fetch_dataset(waves_source, pj(output_path, "waves"), rename_metadata_to="waves_datapackage.json")

    print("Directory structure created and datasets fetched.")

    print("Finalizing datapackage.json...")
    finalize_domain_package(
        domain_path=Path(output_path),
        domain_name=domain_name,
        spatial_source=spatial_source,
        dhw_source=dhw_source,
        connectivity_source=connectivity_source,
        icc_source=icc_source,
        cyclones_source=cyclones_source,
        waves_source=waves_source
    )

    typer.secho("\nDomain built successfully.", fg=typer.colors.GREEN, bold=True)
    typer.echo("Note: You must manually update the generated 'datapackage.json' to specify")
    typer.echo("      column names for the spatial resource (location_id_col, cluster_id_col,")
    typer.echo("      k_col, and area_col) to ensure compatibility with ADRIA.")
    typer.echo("      You should also create a README.md to describe the domain.")


