import typer
from pathlib import Path
from rrap_dg.format.formatters import (
    rme_connectivity,
    standard_netcdf_dhw,
    rme_dhw,
    rme_icc
)
from rrap_dg.format.packaging import finalize_dataset
from rrap_dg.utils import validate_metadata_presence

app = typer.Typer()

@app.command(name="rme-connectivity")
def rme_connectivity_cmd(
    input_path: str = typer.Option(..., help="Path to input connectivity data (dir with CSVs or root)."),
    output_path: str = typer.Option(..., help="Output directory."),
    canonical_path: str = typer.Option(..., help="Path to canonical spatial geopackage."),
    connectivity_pattern: str = typer.Option("**/data_files/con_csv/CONNECT_ACRO*.csv", help="Glob pattern for connectivity CSVs."),
    id_list_pattern: str = typer.Option("**/data_files/id/id_list_*.csv", help="Glob pattern for ID list CSV.")
):
    """
    Format RME Connectivity data.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.") 
    print("Checking for Canonical metadata.json file.")
    found = validate_metadata_presence(Path(canonical_path))
    if found: print("  Found metadata.json.") 
    
    print("Running rme-connectivity formatting...")
    res_name, res_desc, res_fmt = rme_connectivity(
        input_path=input_path,
        output_path=output_path,
        canonical_path=canonical_path,
        connectivity_pattern=connectivity_pattern,
        id_list_pattern=id_list_pattern
    )
    
    finalize_dataset(
        output_path, 
        {"input": input_path, "canonical_spatial": canonical_path}, 
        formatter_name="RME Connectivity",
        resource_name=res_name,
        resource_description=res_desc,
        resource_format=res_fmt
    )

@app.command(name="standard-dhw")
def standard_dhw_cmd(
    input_path: str = typer.Option(..., help="Path to input NetCDF DHW files."),
    output_path: str = typer.Option(..., help="Output directory."),
    rcps: str = typer.Option("2.6 4.5 7.0 8.5", help="Space-separated list of RCPs."),
    timeframe: str = typer.Option("2025 2099", help="Timeframe 'YYYY YYYY'."),
    filename_template: str = typer.Option("*{ssp}*", help="Glob template for finding files.")
):
    """
    Format standard NetCDF DHW files.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.") 
    
    print("Running standard-dhw formatting...")
    res_name, res_desc, res_fmt = standard_netcdf_dhw(
        input_path=input_path,
        output_path=output_path,
        rcps=rcps,
        timeframe=timeframe,
        filename_template=filename_template
    )
    finalize_dataset(
        output_path, 
        {"input": input_path}, 
        formatter_name="Standard NetCDF DHW",
        resource_name=res_name,
        resource_description=res_desc,
        resource_format=res_fmt
    )

@app.command(name="rme-dhw")
def rme_dhw_cmd(
    input_path: str = typer.Option(..., help="Path to input RME DHW CSVs."),
    output_path: str = typer.Option(..., help="Output directory."),
    canonical_path: str = typer.Option(..., help="Path to canonical spatial geopackage."),
    rcps: str = typer.Option("2.6 4.5 7.0 8.5", help="Space-separated list of RCPs."),
    timeframe: str = typer.Option("2025 2099", help="Timeframe 'YYYY YYYY'."),
    dhw_csv_pattern: str = typer.Option("**/data_files/dhw_csv/*.csv", help="Glob pattern for DHW CSVs.")
):
    """
    Format RME DHW CSVs to NetCDF.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.") 
    print("Checking for Canonical metadata.json file.")
    found = validate_metadata_presence(Path(canonical_path))
    if found: print("  Found metadata.json.") 
    
    print("Running rme-dhw formatting...")
    res_name, res_desc, res_fmt = rme_dhw(
        input_path=input_path,
        output_path=output_path,
        canonical_path=canonical_path,
        rcps=rcps,
        timeframe=timeframe,
        dhw_csv_pattern=dhw_csv_pattern
    )
    finalize_dataset(
        output_path, 
        {"input": input_path, "canonical_spatial": canonical_path}, 
        formatter_name="RME DHW",
        resource_name=res_name,
        resource_description=res_desc,
        resource_format=res_fmt
    )

@app.command(name="rme-icc")
def rme_icc_cmd(
    input_path: str = typer.Option(..., help="Path to input RME ICC data."),
    output_path: str = typer.Option(..., help="Output directory."),
    canonical_path: str = typer.Option(..., help="Path to canonical spatial geopackage.")
):
    """
    Format RME Initial Coral Cover (ICC) using Julia.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.") 
    print("Checking for Canonical metadata.json file.")
    found = validate_metadata_presence(Path(canonical_path))
    if found: print("    Found metadata.json.") 
    
    print("Running rme-icc formatting...")
    res_name, res_desc, res_fmt = rme_icc(
        input_path=input_path,
        output_path=output_path,
        canonical_path=canonical_path
    )
    finalize_dataset(
        output_path, 
        {"input": input_path, "canonical_spatial": canonical_path}, 
        formatter_name="RME ICC",
        resource_name=res_name,
        resource_description=res_desc,
        resource_format=res_fmt
    )
