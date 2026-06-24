import typer
import juliacall
import geopandas as gpd
import pandas as pd
from pathlib import Path
from rrap_dg import PKG_PATH


jl = juliacall.newmodule("DomainClustering")
jl.seval(f'include("{PKG_PATH}/cluster_domain/domain_clustering.jl")')

app = typer.Typer()

@app.command(help="Create new geopackage file with clustered locations")
def cluster(
    gpkg_path: str,
    output_path: str,
) -> None:
    jl.cluster(gpkg_path, output_path)

@app.command(name="prepare", help="Prepare cluster geopackage (force EPSG:4326, resolve site ID columns, and map calibration groups / carrying capacities)")
def prepare(
    cluster_gpkg: str = typer.Option(..., help="Path to the cluster geopackage."),
    canonical_gpkg: str = typer.Option(..., help="Path to the canonical geopackage."),
    output_path: str = typer.Option(None, help="Path to save the updated cluster geopackage. If not provided, it will overwrite the input cluster geopackage."),
) -> None:
    print(f"Loading cluster geopackage: {cluster_gpkg}")
    cluster_gdf = gpd.read_file(cluster_gpkg)
    
    # 1. Force EPSG:4326 alignment
    if cluster_gdf.crs != "EPSG:4326":
        print(f"Reprojecting cluster geopackage from {cluster_gdf.crs} to EPSG:4326...")
        cluster_gdf = cluster_gdf.to_crs(epsg=4326)
        
    print(f"Loading canonical geopackage: {canonical_gpkg}")
    canonical_gdf = gpd.read_file(canonical_gpkg)
    
    # 2. Resolve site ID column variation (site_id -> reef_siteid)
    if "reef_siteid" not in cluster_gdf.columns and "site_id" in cluster_gdf.columns:
        print("Normalizing 'site_id' column to 'reef_siteid'...")
        cluster_gdf.rename(columns={"site_id": "reef_siteid"}, inplace=True)
        
    if "reef_siteid" not in cluster_gdf.columns:
        print("Error: reef_siteid not found in cluster geopackage.")
        raise typer.Exit(code=1)
        
    if "GBRMPA_ID" not in canonical_gdf.columns:
        print("Error: GBRMPA_ID not found in canonical geopackage.")
        raise typer.Exit(code=1)
    if "CB_CALIB_GROUPS" not in canonical_gdf.columns:
        print("Error: CB_CALIB_GROUPS not found in canonical geopackage.")
        raise typer.Exit(code=1)

    # Prepare canonical mapping: GBRMPA_ID normalized (e.g., 14-116b -> 14116B)
    print("Preparing canonical mapping...")
    canonical_gdf["NORM_GBRMPA"] = canonical_gdf["GBRMPA_ID"].str.replace("-", "").str.upper()
    # Use first available calibration group for each normalized ID
    gbrmpa_mapping = canonical_gdf.groupby("NORM_GBRMPA")["CB_CALIB_GROUPS"].first().to_dict()
    
    # 1. Map via reef_siteid (e.g., Lizard_14116B_Crest_1 -> 14116B)
    print("Mapping via reef_siteid...")
    cluster_gdf["EXTRACTED_GBRMPA"] = cluster_gdf["reef_siteid"].str.split("_").str[1].str.upper()
    cluster_gdf["CB_CALIB_GROUPS"] = cluster_gdf["EXTRACTED_GBRMPA"].map(gbrmpa_mapping)
    
    # 2. Fallback to UNIQUE_ID prefix if reef_siteid mapping failed
    missing_mask = cluster_gdf["CB_CALIB_GROUPS"].isna()
    num_missing = missing_mask.sum()
    
    if num_missing > 0:
        print(f"Found {num_missing} missing matches. Attempting UNIQUE_ID fallback...")
        
        # Prepare fallback mapping from canonical UNIQUE_IDs
        # Map full UNIQUE_ID
        direct_mapping = canonical_gdf.set_index("UNIQUE_ID")["CB_CALIB_GROUPS"].to_dict()
        cluster_gdf.loc[missing_mask, "CB_CALIB_GROUPS"] = cluster_gdf.loc[missing_mask, "UNIQUE_ID"].astype(str).map(direct_mapping)
        
        # Still missing? Try stripping last 2 digits of UNIQUE_ID
        still_missing_mask = cluster_gdf["CB_CALIB_GROUPS"].isna()
        if still_missing_mask.any():
            print(f"Attempting prefix fallback (stripping last 2 digits)...")
            canonical_gdf["ID_PREFIX"] = canonical_gdf["UNIQUE_ID"].astype(str).str[:-2]
            prefix_mapping = canonical_gdf.groupby("ID_PREFIX")["CB_CALIB_GROUPS"].first().to_dict()
            
            cluster_gdf.loc[still_missing_mask, "ID_PREFIX"] = cluster_gdf.loc[still_missing_mask, "UNIQUE_ID"].astype(str).str[:-2]
            cluster_gdf.loc[still_missing_mask, "CB_CALIB_GROUPS"] = cluster_gdf.loc[still_missing_mask, "ID_PREFIX"].map(prefix_mapping)
            cluster_gdf.drop(columns=["ID_PREFIX"], inplace=True)

    # Cleanup internal mapping columns
    if "EXTRACTED_GBRMPA" in cluster_gdf.columns:
        cluster_gdf.drop(columns=["EXTRACTED_GBRMPA"], inplace=True)
    
    # Fill missing CB_CALIB_GROUPS with 0
    num_missing_groups = cluster_gdf["CB_CALIB_GROUPS"].isna().sum()
    if num_missing_groups > 0:
        print(f"Replacing {num_missing_groups} missing CB_CALIB_GROUPS with 0.")
        cluster_gdf["CB_CALIB_GROUPS"] = cluster_gdf["CB_CALIB_GROUPS"].fillna(0)
    
    # Fill missing k values with 0
    if "k" in cluster_gdf.columns:
        num_missing_k = cluster_gdf["k"].isna().sum()
        if num_missing_k > 0:
            print(f"Replacing {num_missing_k} missing 'k' values with 0.")
            cluster_gdf["k"] = cluster_gdf["k"].fillna(0)

    print("Final status: All sites have CB_CALIB_GROUPS and k values assigned.")

    save_path = Path(output_path) if output_path else Path(cluster_gpkg)
    layer_name = save_path.stem
    print(f"Saving preprocessed geopackage to: {save_path} (Layer: {layer_name})")
    
    save_path.unlink(missing_ok=True)
    cluster_gdf.to_file(str(save_path), layer=layer_name, driver="GPKG", engine="pyogrio")
    print("Prepare complete.")


@app.command(
    name="update-cb-calib-groups",
    deprecated=True,
    help="Deprecated: Use 'prepare' instead.",
)
def update_cb_calib_groups(
    cluster_gpkg: str = typer.Option(..., help="Path to the cluster geopackage."),
    canonical_gpkg: str = typer.Option(..., help="Path to the canonical geopackage."),
    output_path: str = typer.Option(None, help="Path to save the updated cluster geopackage. If not provided, it will overwrite the input cluster geopackage."),
) -> None:
    print("Warning: 'update-cb-calib-groups' is deprecated. Please use 'prepare' instead.")
    prepare(cluster_gpkg, canonical_gpkg, output_path)
