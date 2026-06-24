import typer
from pathlib import Path
from rrap_dg.format.formatters import (
    rme_connectivity,
    cmip6_downscaled_dhw,
    cmip6_consolidated_mcb_dhw,
    cmip6_mcb_dhw_prepend,
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

@app.command(name="cmip6-downscaled-dhw")
def cmip6_downscaled_dhw_cmd(
    input_path: str = typer.Option(..., help="Path to input NetCDF DHW files."),
    output_path: str = typer.Option(..., help="Output directory."),
    rcps: str = typer.Option("2.6 4.5 7.0 8.5", help="Space-separated list of RCPs."),
    timeframe: str = typer.Option("2025 2099", help="Timeframe 'YYYY YYYY'."),
    filename_template: str = typer.Option("*{ssp}*", help="Glob template for finding files."),
    variable_name: str = typer.Option("dhw_max", help="Variable name in the NetCDF files.")
):
    """
    Format CMIP6 Statistically Downscaled NetCDF DHW files.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.") 
    
    print("Running cmip6-downscaled-dhw formatting...")
    res_name, res_desc, res_fmt = cmip6_downscaled_dhw(
        input_path=input_path,
        output_path=output_path,
        rcps=rcps,
        timeframe=timeframe,
        filename_template=filename_template,
        variable_name=variable_name
    )
    finalize_dataset(
        output_path, 
        {"input": input_path}, 
        formatter_name="CMIP6 Statistically Downscaled DHW",
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


@app.command(name="cmip6-consolidated-mcb")
def cmip6_consolidated_mcb_cmd(
    input_path: str = typer.Option(..., help="Path to root of raw MCB NetCDF files."),
    output_path: str = typer.Option(..., help="Output directory."),
    region: str = typer.Option(..., help="Region name (e.g., 'Cairns' or 'GBR')."),
    hist_timeframe: str = typer.Option("2007 2014", help="Historical timeframe 'YYYY YYYY'."),
    proj_timeframe: str = typer.Option("2015 2100", help="Projection timeframe 'YYYY YYYY'.")
):
    """
    Consolidate raw MCB NetCDF files into a 5D NetCDF with historical prepend.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.")

    print(f"Running cmip6-consolidated-mcb formatting for {region}...")
    res_name, res_desc, res_fmt = cmip6_consolidated_mcb_dhw(
        input_path=input_path,
        output_path=output_path,
        region=region,
        hist_timeframe=hist_timeframe,
        proj_timeframe=proj_timeframe
    )
    finalize_dataset(
        output_path,
        {"input": input_path},
        formatter_name="CMIP6 Consolidated MCB DHW",
        resource_name=res_name,
        resource_description=res_desc,
        resource_format=res_fmt
    )


@app.command(name="cmip6-mcb-prepend")
def cmip6_mcb_prepend_cmd(
    input_path: str = typer.Option(..., help="Path to root of raw MCB NetCDF files."),
    output_path: str = typer.Option(..., help="Output directory."),
    region: str = typer.Option(..., help="Region name (e.g., 'Cairns' or 'GBR')."),
    albedo: str = typer.Option("0.3", help="Albedo value (e.g. 0.2, 0.3)."),
    mcb_duration: int = typer.Option(150, help="MCB duration (0, 50, 100, 150)."),
    hist_timeframe: str = typer.Option("2007 2014", help="Historical timeframe 'YYYY YYYY'."),
    proj_timeframe: str = typer.Option("2015 2100", help="Projection timeframe 'YYYY YYYY'.")
):
    """
    Format 3D MCB DHW NetCDFs with historical data prepended.
    """
    print("Checking for Input metadata.json file.")
    found = validate_metadata_presence(Path(input_path))
    if found: print("  Found metadata.json.")

    print(f"Running cmip6-mcb-prepend for {region} | Alb {albedo} | MCB {mcb_duration}d...")
    res_name, res_desc, res_fmt = cmip6_mcb_dhw_prepend(
        input_path=input_path,
        output_path=output_path,
        region=region,
        albedo=albedo,
        mcb_duration=mcb_duration,
        hist_timeframe=hist_timeframe,
        proj_timeframe=proj_timeframe
    )
    finalize_dataset(
        output_path,
        {"input": input_path},
        formatter_name="CMIP6 MCB Prepend DHW",
        resource_name=res_name,
        resource_description=res_desc,
        resource_format=res_fmt
    )
