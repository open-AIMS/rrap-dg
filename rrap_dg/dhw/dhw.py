import warnings
import re
from os.path import join as pj
from glob import glob

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.stats import genextreme as gev

import xarray as xr
import rasterio as rio
import rioxarray as rxr

import netCDF4
import datapackage as dpkg
import typer

from rich.progress import track

from .dhw_funcs import (
    detrended_max_DHW,
    get_DHW_trend,
    get_closest_datapoint,
    gauss,
    extract_DHW_pattern,
)


app = typer.Typer()


@app.command(help="Generate Degree Heating Week datasets")
def generate(
    input_loc: str,
    output_loc: str,
    n_sims: int = 50,
    RCPs: str = typer.Option("2.6 4.5 6.0 8.5"),
    gen_year: str = typer.Option("2025 2100"),
) -> None:
    """Produce Degree Heating Week projections for a given cluster.

    Parameters
    ----------
    input_loc : str, location of dataset
    output_loc : str, output location of generated netCDFs
    n_sims : int, number of members to generate
    RCPs : str, of RCP scenarios to generate members for
    gen_year : str, the time frame member projections should be
        generated for (end exclusive). Defaults to (2025, 2100).

    Notes
    -----
    Some acronyms used throughout.

    CRW : Coral Reef Watch
    RCP : Representative Concentration Pathway
    """
    md = dpkg.DataPackage(pj(input_loc, "datapackage.json"))

    RCPs = tuple(RCPs.split(" "))
    gen_year = tuple(map(int, gen_year.split(" ")))

    # TODO: Leverage metadata in datapackage.json to identify all data files
    #       Currently only the cluster name is extracted.
    cluster = md.descriptor["name"]

    # Get historical NOAA data
    hist_dhw_data = xr.open_dataset(pj(input_loc, "NOAA", "GBR_dhw_hist_noaa.nc"))
    crs_code = hist_dhw_data.attrs["geospatial_bounds_crs"]
    hist_dhw_data = hist_dhw_data.rio.write_crs(crs_code)

    # Read spatial data and ensure CRS matches
    cluster_site = gpd.read_file(pj(input_loc, "spatial", f"{cluster}.gpkg")).to_crs(
        crs_code
    )

    # Clunky way of getting the scale factor
    # There's probably a better way
    with rxr.open_rasterio(pj(input_loc, "NOAA", "GBR_dhw_hist_noaa.nc")) as ds:
        scale_factor = ds.attrs["scale_factor"]

    # Extract target area from historic dataset
    with rio.open(pj(input_loc, "NOAA", "GBR_dhw_hist_noaa.nc")) as src:
        cluster_site_dhw, out_transform = rio.mask.mask(
            src, cluster_site.geometry, all_touched=True, filled=False, crop=True
        )
        # out_meta = src.meta

        # Manually apply scale factor
        cluster_site_dhw *= scale_factor

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Ignore warnings that centroids are incorrect.
        # This is because WGS84 is not a projected CRS
        # but we assume everything lines up...
        lon = cluster_site.centroid.x.to_numpy()
        lat = cluster_site.centroid.y.to_numpy()

    site_lonlat = np.array((lon, lat)).T

    n_sites = cluster_site.shape[0]
    gen_year_tf = list(range(*gen_year))
    n_years = len(gen_year_tf)

    rcp_match = {"2.6": "26", "4.5": "45", "6.0": "60", "8.5": "85"}

    # Load in GBR-wide reef positions
    gbr_reefs = pd.read_csv(pj(input_loc, "spatial", "list_gbr_reefs.csv"))
    gbr_reef_lon = gbr_reefs["LON"].to_numpy()
    gbr_reef_lat = gbr_reefs["LAT"].to_numpy()

    # Load yearly DHW data for cluster
    recom_files = glob(pj(input_loc, "RECOM", f"{cluster}*_*_dhw*.nc"))
    recom_data = extract_DHW_pattern(recom_files)
    dhw_pattern, mean_dhw_pattern, recom_lon, recom_lat = recom_data

    # Create paired lon/lats, truncated to 4 decimal places so it matches
    # GBR reef data read in from a CSV.
    # Can be used with the original `inpoly()` method if needed (but not recommended).
    recom_lonlats = np.array(
        list(
            zip(
                [float(f"{rd:.4f}") for rd in recom_lon.flatten()],
                [float(f"{rd:.4f}") for rd in recom_lat.flatten()],
            )
        )
    )

    # Regex rule to identify projection timeframe
    cmp = re.compile(r"([0-9]{4})_([0-9]{4})")

    # Flip dimension order for consistency with MATLAB
    # (gets read in as: timesteps, sites, sims)
    dhw = np.zeros((n_sims, site_lonlat.shape[0], n_years))

    # Projected data (MIROC5) does not have any spatial metadata
    # so align datasets using the lat/longs
    # Create lon/lat index for GBR data
    # (used to align MIROC data)
    lonlat_index = pd.MultiIndex.from_tuples(
        zip(gbr_reef_lon, gbr_reef_lat), names=["lon", "lat"]
    )

    # Identify common locations
    f_recom_lons, f_recom_lats = list(zip(*recom_lonlats))
    common_lons = np.intersect1d(f_recom_lons, gbr_reef_lon)
    common_lats = np.intersect1d(f_recom_lats, gbr_reef_lat)

    # for rcp_i in track(range(len(RCPs)), description="Generating members..."):
    for rcp_i in range(len(RCPs)):
        RCP = RCPs[rcp_i]
        RCP_name = rcp_match[RCP]

        proj_fn = f"GBR_maxDHW_MIROC5_rcp{RCP_name}_2021_2099.csv"

        # Extract projected timeframe from filename
        proj_range = cmp.findall(proj_fn)[0]
        proj_range = (int(proj_range[0]), int(proj_range[1]) + 1)

        # Get projection trend
        MIROC_data = pd.read_csv(pj(input_loc, "MIROC5", proj_fn), header=None)
        MIROC_data.index = lonlat_index

        # Convert DataFrame to xarray dataset
        MIROC_data = xr.Dataset.from_dataframe(MIROC_data)
        MIROC_data["time"] = pd.to_datetime(list(range(*proj_range)), format="%Y")

        # WARNING: Assumes order of locations align with NOAA dataset.
        #          Original approach attempted to match up locations
        #          based on index positions. The line below uses the
        #          lon/lat values
        #              >>> MIROC_data.loc[(common_lons, common_lats), :]
        #
        #          Both identify a single cell (suspicious?).
        #
        #          Lon/lat of original approach: 146.1809 -16.803
        #          This approach:                146.2486 -16.9116
        #          Mean difference (orig - new): 0.13649
        #
        #          A more robust approach would be to leverage
        #          xarray instead (the approach used below).
        #          However, this identifies a larger area
        #          15x4, as opposed to the 1x1 area.

        # Get the mean DHW timeseries within our cluster domain
        mean_proj_dhw = MIROC_data.sel({"lon": common_lons, "lat": common_lats}).mean()
        mean_proj_dhw = mean_proj_dhw.to_array().values

        domain_hist_dhw = hist_dhw_data.sel(
            {"longitude": common_lons, "latitude": common_lats}, method="nearest"
        )
        mean_hist_dhw = domain_hist_dhw.mean(dim=("longitude", "latitude"))

        dens_prob, max_DHW_detrend = detrended_max_DHW(
            mean_hist_dhw, mean_proj_dhw, gen_year_tf, proj_range
        )

        # Take a stochastically generated number within the yearly density
        # probabilities for each year and each simulation
        dhw_rand = np.zeros((n_sims, n_years))
        for yr in range(n_years):
            dhw_rand[:, yr] = gev.rvs(*dens_prob[yr], size=(n_sims))

        dist97 = gev.ppf(0.97, *dens_prob[0])

        # Apply spatial adjustment
        for site_i in range(site_lonlat.shape[0]):
            # Find data closest to this site's coordinates
            target_lonlat = (site_lonlat[site_i, 0], site_lonlat[site_i, 1])
            closest_dhw = get_closest_datapoint(
                target_lonlat, recom_lonlats, dhw_pattern
            )

            # Define the spatial adjustment as the difference from the mean within
            # the cluster domain.
            spatialadj = closest_dhw - mean_dhw_pattern

            # Get the location specific trend lat/lon and MIROC5 trend
            gauss_fit_site = get_DHW_trend(domain_hist_dhw, mean_proj_dhw, proj_range)

            # The first timeseries needs to be the exact MIROC5 projection
            # (MIROC5 data starts from 2021)
            dhw[0, site_i, :] = mean_proj_dhw[
                gen_year_tf[0] - proj_range[0] : (gen_year_tf[-1] - proj_range[0] + 1)
            ]

            # Produce the simulations timeseries
            # Superimpose the density probability function over the mean trend in
            # the historical data and MIROC5 projection, and the spatial adjustment
            # Simulations starts at 2 because the first simulation is the exact
            # MIROC5 simulation
            for sim_i in range(1, n_sims):
                for year_i in gen_year_tf:
                    yr_s = year_i - gen_year_tf[0]

                    # Run a safety check, if the data is higher than any data in
                    # the annual distribution, choose another number (the
                    # distribution function doesn't have an upper limit, so we cut
                    # it off to avoid very large unreasonable numbers)
                    while dhw_rand[sim_i, yr_s] > np.max(max_DHW_detrend[:, yr_s]):
                        dhw_rand[sim_i, yr_s] = gev.rvs(*dens_prob[yr_s])

                    # Adjust the spatial adjustment term according to relative
                    # intensity compared to the first time step's data distribution
                    # (as the trend increases, DHW above the first step's maximum
                    # automatically get 100% of the spatial pattern.
                    dhw_r = dhw_rand[sim_i, yr_s] + gauss(yr_s, *gauss_fit_site)
                    if dhw_r >= dist97:
                        spatial_adjyr = spatialadj
                    else:
                        spatial_adjyr = spatialadj * (dhw_r / dist97)

                    dhw[sim_i, site_i, yr_s] = dhw_r + spatial_adjyr

            # Make values > 0 as negative DHW is not possible.
            dhw = np.maximum(dhw, 0.0)

        # Save to a netcdf file
        output_file = pj(output_loc, f"dhw_RCP{RCP_name}.nc")
        with netCDF4.Dataset(output_file, "w", format="NETCDF4") as nc_out:
            # Define dimensions
            nc_out.createDimension("member", n_sims)
            nc_out.createDimension("sites", n_sites)
            nc_out.createDimension("timesteps", n_years)

            # Define Variables
            lon_ID = nc_out.createVariable("longitude", "f8", ("sites",))
            lat_ID = nc_out.createVariable("latitude", "f8", ("sites",))
            reef_ID = nc_out.createVariable("reef_siteid", str, ("sites",))
            unique_ID = nc_out.createVariable("UNIQUE_ID", str, ("sites",))
            dhw_ID = nc_out.createVariable(
                "dhw", "f8", ("member", "sites", "timesteps")
            )  # variable order flipped for consistency with MATLAB

            # Put attributes
            # latitude
            lon_ID.coordinates = "sites"
            lat_ID.units = "degrees_north"
            lat_ID.long_name = "latitude"
            lat_ID.standard_name = "latitude"
            lat_ID.projection = crs_code

            # longitude
            lon_ID.coordinates = "sites"
            lon_ID.units = "degrees_east"
            lon_ID.long_name = "longitude"
            lon_ID.standard_name = "longitude"
            lon_ID.projection = crs_code

            # reef_siteid
            reef_ID.coordinates = "sites"
            reef_ID.units = ""
            reef_ID.long_name = "reef site id"
            reef_ID.standard_name = "reef_site_id"

            # unique_id
            unique_ID.coordinates = "sites"
            unique_ID.units = ""
            unique_ID.long_name = "unique id"
            unique_ID.standard_name = "unique_id"

            # DHW data
            dhw_ID.coordinates = "timesteps sites members"
            dhw_ID.units = "DegC-week"
            dhw_ID.long_name = "degree heating week"
            dhw_ID.standard_name = "DHW"
            dhw_ID.missing_value = 1.0e35

            # Put the variables' values
            lon_ID[:] = lon
            lat_ID[:] = lat
            reef_ID[:] = cluster_site.loc[:, "reef_siteid"].to_numpy()
            unique_ID[:] = cluster_site.loc[:, "UNIQUE_ID"].to_numpy().astype("str")
            dhw_ID[:] = dhw


# if __name__ == "__main__":
#     typer.run(generate_DHWs)
#     generate_DHWs("C:/development/ADRIA_data/DHW", "C:/development/ADRIA_data/DHW")
