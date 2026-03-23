import warnings
import re
import psutil
import os
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
    create_max_DHW,
    get_closest_data,
    fit_gauss,
    gauss,
    extract_DHW_pattern,
)


app = typer.Typer()


def print_mem(label: str):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"[{label}] RAM Used: {mem_mb:.2f} MiB")


@app.command(help="Generate Degree Heating Week datasets")
def generate(
    cluster_name: str,
    input_loc: str,
    output_loc: str,
    n_sims: int = 50,
    RCPs: str = typer.Option("2.6 4.5 6.0 8.5"),
    gen_year: str = typer.Option("2025 2100"),
    gpkg_path: str = typer.Option(None, help="Direct path to the cluster geopackage file."),
    recom_dir: str = typer.Option(None, help="Direct path to the directory containing RECOM files."),
) -> None:
    """Produce Degree Heating Week projections for a given cluster.

    Note: This process is very memory intensive (~20GB peak usage) and time consuming
          (10s of minutes but generally < 1 hour).

    Parameters
    ----------
    cluster_name : str, name of geopackage file to use (typically same as reef cluster name)
    input_loc : str, location of dataset
    output_loc : str, output location of generated netCDFs
    n_sims : int, number of members to generate
    RCPs : str, of RCP scenarios to generate members for
    gen_year : str, the time frame member projections should be
        generated for (end exclusive). Defaults to (2025, 2100).
    gpkg_path : str, direct path to the cluster geopackage file.
    recom_dir : str, direct path to the directory containing RECOM files.

    Notes
    -----
    Some acronyms used throughout.

    CRW : Coral Reef Watch
    RCP : Representative Concentration Pathway
    """
    print_mem("Start")
    
    # TODO: Leverage metadata in datapackage.json to identify all data files
    #       Currently only the cluster name is extracted.
    # md = dpkg.DataPackage(pj(input_loc, "datapackage.json"))

    RCPs = tuple(RCPs.split(" "))
    gen_year = tuple(map(int, gen_year.split(" ")))

    # Get historical NOAA data
    hist_dhw_data = xr.open_dataset(pj(input_loc, "NOAA", "GBR_dhw_hist_noaa.nc"))
    crs_code = hist_dhw_data.attrs["geospatial_bounds_crs"]
    hist_dhw_data = hist_dhw_data.rio.write_crs(crs_code)
    print_mem("After NOAA Load")

    # Read spatial data and ensure CRS matches
    _gpkg_path = gpkg_path if gpkg_path else pj(input_loc, "spatial", f"{cluster_name}.gpkg")
    cluster_poly = gpd.read_file(_gpkg_path).to_crs(crs_code)
    print_mem("After Geopackage Load")

    # Clunky way of getting the scale factor
    # There's probably a better way
    with rxr.open_rasterio(pj(input_loc, "NOAA", "GBR_dhw_hist_noaa.nc")) as ds:
        scale_factor = ds.attrs["scale_factor"]

    # Extract target area from historic dataset
    with rio.open(pj(input_loc, "NOAA", "GBR_dhw_hist_noaa.nc")) as src:
        cluster_hist_dhw, out_transform = rio.mask.mask(
            src, cluster_poly.geometry, all_touched=True, filled=False, crop=True
        )
        # out_meta = src.meta

        # Manually apply scale factor
        cluster_hist_dhw *= scale_factor

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Ignore warnings that centroids are incorrect.
        # This is because WGS84 is not a projected CRS
        # but we assume everything lines up...
        c_lon = cluster_poly.centroid.x.to_numpy()
        c_lat = cluster_poly.centroid.y.to_numpy()

    cluster_lonlats = np.array((c_lon, c_lat)).T

    n_sites = cluster_poly.shape[0]
    gen_year_tf = list(range(*gen_year))
    n_years = len(gen_year_tf)

    rcp_match = {"2.6": "26", "4.5": "45", "6.0": "60", "8.5": "85"}

    # Load in GBR-wide reef positions
    # TODO: Switch to using the geopackage!
    gbr_reefs = pd.read_csv(pj(input_loc, "spatial", "list_gbr_reefs.csv"))
    gbr_reef_lon = gbr_reefs["LON"].to_numpy()
    gbr_reef_lat = gbr_reefs["LAT"].to_numpy()
    # gbr_reef_lonlats = np.array(list(zip(gbr_reef_lon, gbr_reef_lat)))

    # Load yearly DHW data for cluster
    _recom_dir = recom_dir if recom_dir else pj(input_loc, "RECOM")
    recom_files = glob(pj(_recom_dir, f"*{cluster_name}*_*_dhw*.nc"))
    recom_data = extract_DHW_pattern(recom_files)
    dhw_pattern, mean_dhw_pattern, recom_lon, recom_lat = recom_data
    print_mem("After RECOM Load")

    if np.isnan(mean_dhw_pattern):
        print("WARNING: mean_dhw_pattern is NaN")

    # Regex rule to identify projection timeframe
    cmp = re.compile(r"([0-9]{4})_([0-9]{4})")

    # Flip dimension order for consistency with MATLAB
    # (gets read in as: timesteps, sites, sims)
    dhw = np.zeros((n_sims, cluster_lonlats.shape[0], n_years))

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

    for rcp_i in track(range(len(RCPs)), description="Generating members..."):
        RCP = RCPs[rcp_i]
        RCP_name = rcp_match[RCP]

        proj_fn = f"GBR_maxDHW_MIROC5_rcp{RCP_name}_2021_2099.csv"

        # Extract projected timeframe from filename
        proj_range = cmp.findall(proj_fn)[0]
        proj_range = (int(proj_range[0]), int(proj_range[1]) + 1)

        # Prep projected data
        # TODO: Get file location from datapackage
        p_df = pd.read_csv(pj(input_loc, "MIROC5", proj_fn), header=None)
        print_mem(f"RCP {RCP}: After MIROC5 CSV Load")

        # Vectorized nearest neighbor search for all cluster sites in the MIROC5 list
        # We find the indices of the GBR-wide sites closest to each of our cluster sites.
        gbr_reef_lonlats = np.array(list(zip(gbr_reef_lon, gbr_reef_lat)))
        cluster_site_indices = []
        for c_lon_i, c_lat_i in zip(c_lon, c_lat):
            # Sum of absolute differences (Manhattan distance) for speed
            dists = np.abs(gbr_reef_lonlats[:, 0] - c_lon_i) + np.abs(gbr_reef_lonlats[:, 1] - c_lat_i)
            cluster_site_indices.append(np.argmin(dists))
        
        # Extract projected data for only the sites in our cluster and take the max trend
        cluster_proj_data = p_df.iloc[cluster_site_indices].values
        proj_domain_mean_dhw = np.max(cluster_proj_data, axis=0)
        print_mem(f"RCP {RCP}: After Cluster Data Subset")

        # historic data constrained to area of interest
        # Convert coordinates to Xarray data arrays for vectorized selection
        # This returns a 1D list of values for the sites, not a 2D spatial grid.
        lons_da = xr.DataArray(c_lon, dims="locations")
        lats_da = xr.DataArray(c_lat, dims="locations")
        
        hist_domain_dhw = hist_dhw_data.sel(
            longitude=lons_da, latitude=lats_da, method="nearest"
        )
        print_mem(f"RCP {RCP}: After hist_domain_dhw.sel (Vectorized)")
        
        hist_domain_mean_dhw = hist_domain_dhw.mean(dim="locations").squeeze()

        dens_prob, domain_max_DHW_detrend = detrended_max_DHW(
            hist_domain_mean_dhw, proj_domain_mean_dhw, gen_year_tf, proj_range
        )

        # Take a stochastically generated number within the yearly density
        # probabilities for each year and each simulation
        dhw_rand = np.zeros((n_sims, n_years))
        for yr in range(n_years):
            dhw_rand[:, yr] = gev.rvs(*dens_prob[yr], size=n_sims)

        dist97 = gev.ppf(0.97, *dens_prob[0])

        if np.isnan(dist97):
            print(f"WARNING: dist97 is NaN for RCP {RCP}")

        # Get identified lon/lats for the specific sites
        domain_lonlats = np.array(
            list(
                zip(
                    hist_domain_dhw.longitude.values,
                    hist_domain_dhw.latitude.values,
                )
            )
        )

        # Apply spatial adjustment
        for site_i in range(cluster_lonlats.shape[0]):
            if site_i % 50 == 0:
                print_mem(f"RCP {RCP}: Site {site_i}/{cluster_lonlats.shape[0]}")
            # Find data closest to this site's coordinates
            site_lonlats = (cluster_lonlats[site_i, 0], cluster_lonlats[site_i, 1])
            closest_dhw_ds = get_closest_data(site_lonlats, recom_lonlats, dhw_pattern)
            closest_dhw = (
                closest_dhw_ds
                .to_array()
                .data.mean()
            )

            # Define the spatial adjustment as the difference from the mean within
            # the cluster domain.
            spatialadj = closest_dhw - mean_dhw_pattern

            # Get the location specific trend lat/lon and MIROC5 trend
            # The historical data for this site is now directly indexable
            # We use isel to keep it as an Xarray object with coordinates
            hist_dhw_ts = hist_domain_dhw.isel(locations=site_i)

            # Get projected DHW trend
            _, combined_timeframe, combined_dhw_data = create_max_DHW(
                hist_dhw_ts, proj_domain_mean_dhw, proj_range
            )
            
            gauss_fit_site = fit_gauss(combined_timeframe, combined_dhw_data)

            # The first timeseries needs to be the exact MIROC5 projection
            # (MIROC5 data starts from 2021)
            dhw[0, site_i, :] = proj_domain_mean_dhw[
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
                    while dhw_rand[sim_i, yr_s] > np.max(
                        domain_max_DHW_detrend[:, yr_s]
                    ):
                        dhw_rand[sim_i, yr_s] = gev.rvs(*dens_prob[yr_s])

                    # Adjust the spatial adjustment term according to relative
                    # intensity compared to the first time step's data distribution
                    # (as the trend increases, DHW above the first step's maximum
                    # automatically get 100% of the spatial pattern.
                    dhw_r = dhw_rand[sim_i, yr_s] + gauss(yr_s, *gauss_fit_site)
                    if dhw_r >= dist97:
                        dhw[sim_i, site_i, yr_s] = dhw_r + spatialadj
                        continue

                    dhw[sim_i, site_i, yr_s] = dhw_r + (spatialadj * (dhw_r / dist97)) 

            if np.isnan(dhw[:, site_i, :]).any():
                if site_i == 0:
                    print(f"WARNING: dhw contains NaNs for site {site_i}, RCP {RCP}")

            # Make values > 0 as negative DHW is not possible.
            dhw = np.maximum(dhw, 0.0)

        # Save to a netcdf file
        output_file = pj(output_loc, f"dhwRCP{RCP_name}.nc")
        with netCDF4.Dataset(output_file, "w", format="NETCDF4") as nc_out:
            # Define dimensions
            nc_out.createDimension("member", n_sims)
            nc_out.createDimension("locations", n_sites)
            nc_out.createDimension("timesteps", n_years)

            # Define Variables
            lon_ID = nc_out.createVariable("longitude", "f8", ("locations",))
            lat_ID = nc_out.createVariable("latitude", "f8", ("locations",))
            reef_ID = nc_out.createVariable("reef_siteid", str, ("locations",))
            unique_ID = nc_out.createVariable("UNIQUE_ID", str, ("locations",))
            dhw_ID = nc_out.createVariable(
                "dhw", "f8", ("member", "locations", "timesteps")
            )  # variable order flipped for consistency with MATLAB

            # Put attributes
            # latitude
            lon_ID.coordinates = "locations"
            lat_ID.units = "degrees_north"
            lat_ID.long_name = "latitude"
            lat_ID.standard_name = "latitude"
            lat_ID.projection = crs_code

            # longitude
            lon_ID.coordinates = "locations"
            lon_ID.units = "degrees_east"
            lon_ID.long_name = "longitude"
            lon_ID.standard_name = "longitude"
            lon_ID.projection = crs_code

            # reef_siteid
            reef_ID.coordinates = "locations"
            reef_ID.units = ""
            reef_ID.long_name = "reef site id"
            reef_ID.standard_name = "reef_site_id"

            # unique_id
            unique_ID.coordinates = "locations"
            unique_ID.units = ""
            unique_ID.long_name = "unique id"
            unique_ID.standard_name = "unique_id"

            # DHW data
            dhw_ID.coordinates = "timesteps locations members"
            dhw_ID.units = "DegC-week"
            dhw_ID.long_name = "degree heating week"
            dhw_ID.standard_name = "DHW"
            dhw_ID.missing_value = 1.0e35

            # Put the variables' values
            lon_ID[:] = c_lon
            lat_ID[:] = c_lat

            # Use 'site_id' if available, otherwise fallback to 'reef_siteid'
            site_id_col = "site_id" if "site_id" in cluster_poly.columns else "reef_siteid"
            reef_ID[:] = cluster_poly.loc[:, site_id_col].to_numpy()

            unique_ID[:] = cluster_poly.loc[:, "UNIQUE_ID"].to_numpy().astype("str")
            dhw_ID[:] = dhw
        
        print_mem(f"RCP {RCP}: After NetCDF Write")
