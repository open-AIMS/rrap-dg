import geopandas as gpd

import typer

app = typer.Typer()

@app.command(help="Format the canonical geopackage for use with ADRIA.")
def format_canonical(
    canonical_path: str,
    output_path: str
) -> None:

    canonical = gpd.read_file(canonical_path)

    reef_siteids = canonical["UNIQUE_ID"]
    cluster_ids = [str(int(el)) for el in canonical["GBRMPA_BIOREGION"]]

    k_vals = canonical["ReefMod_habitable_proportion"]
    area_vals = canonical["ReefMod_area_m2"]

    canonical.insert(0, 'area', area_vals)
    canonical.insert(0, 'k', k_vals)
    canonical.insert(0, 'cluster_id', cluster_ids)
    canonical.insert(0, 'reef_siteid', reef_siteids)

    canonical.to_file(output_path, driver='GPKG', index=False)

    return None
