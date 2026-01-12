import netCDF4
import numpy as np
import pandas as pd

def validate_location_agreement(dhw_nc_handles: list) -> None:
    unique_ids = dhw_nc_handles[0].variables['UNIQUE_ID'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(unique_ids == nc_handle.variables['UNIQUE_ID'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different location UNIQUE_IDs."
            )

    return None

def validate_lon_agreement(dhw_nc_handles: list) -> None:
    lons = dhw_nc_handles[0].variables['lon_reef'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(lons == nc_handle.variables['lon_reef'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different latitude arrays."
            )

    return None

def validate_lat_agreement(dhw_nc_handles: list) -> None:
    lats = dhw_nc_handles[0].variables['lat_reef'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(lats == nc_handle.variables['lat_reef'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different latitude arrays."
            )

    return None

def validate_time_agreement(dhw_nc_handles: list) -> None:
    years = dhw_nc_handles[0].variables['time'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(years == nc_handle.variables['time'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different time arrays."
            )

    return None

def get_time_index(dhw_nc_handle, timeframe: tuple) -> tuple:
    # DHW files have a reference time of 1950-01-01 00:00:00
    start_year = 1950 + round(dhw_nc_handle.variables['time'][0] / 365)
    end_year = 1950 + round(dhw_nc_handle.variables['time'][-1] / 365)

    start_year_sub = timeframe[0]
    end_year_sub = timeframe[1]

    if start_year_sub < start_year or end_year_sub > end_year:
        raise ValueError(
            f"Requested timeframe {timeframe} is outside the file's"
            f"timeframe ({start_year}-{end_year})"
        )

    start_index = start_year_sub - start_year
    end_index = end_year_sub - start_year

    return start_index, end_index

def format_single_rcp_dhw(
        dhw_nc_fps: list[str], output_filepath: str, timeframe: tuple
):
    n_sims = len(dhw_nc_fps)
    n_locs = 3806

    nc_handles = [netCDF4.Dataset(fp) for fp in dhw_nc_fps]
    validate_location_agreement(nc_handles)
    validate_lat_agreement(nc_handles)
    validate_lon_agreement(nc_handles)
    validate_time_agreement(nc_handles)

    start_yr_idx, end_yr_idx = get_time_index(nc_handles[0], timeframe)
    n_years = timeframe[1] - timeframe[0] + 1

    with netCDF4.Dataset(output_filepath, "w", format="NETCDF4") as nc_out:
        # Define Dimensions
        nc_out.createDimension("model", n_sims)
        nc_out.createDimension("locations", n_locs)
        nc_out.createDimension("timesteps", n_years)

        lon_ID = nc_out.createVariable("longitude", "f8", ("locations",))
        lat_ID = nc_out.createVariable("latitude", "f8", ("locations",))
        time_ID = nc_out.createVariable("timesteps", "i4", ("timesteps",))
        GBRMPA_ID = nc_out.createVariable("GBRMPA_ID", str, ("locations",))
        unique_ID = nc_out.createVariable("UNIQUE_ID", str, ("locations",))
        location_ID = nc_out.createVariable("locations", str, ("locations",))
        dhw_ID = nc_out.createVariable(
            "dhw", "f8", ("model", "locations", "timesteps")
        )

        lon_ID.coordinates = "locations"
        lat_ID.units = "degrees_north"
        lat_ID.long_name = "latitude"
        lat_ID.standard_name = "latitude"

        lon_ID.coordinates = "locations"
        lon_ID.units = "degrees_east"
        lon_ID.long_name = "longitude"
        lon_ID.standard_name = "longitude"

        time_ID.coordinates = "timesteps"
        time_ID.units = "year"
        time_ID.long_name = "timesteps"
        time_ID.standard_name = "timesteps"

        GBRMPA_ID.coordinates = "locations"
        GBRMPA_ID.units = ""
        GBRMPA_ID.long_name = "gbrmpa id"
        GBRMPA_ID.standard_name = "gbrmpa_id"

        unique_ID.coordinates = "locations"
        unique_ID.units = ""
        unique_ID.long_name = "unique id"
        unique_ID.standard_name = "unique_id"

        location_ID.coordinates = "locations"
        location_ID.units = ""
        location_ID.long_name = "unique id"
        location_ID.standard_name = "unique_id"

        dhw_ID.coordinates = "timesteps locations members"
        dhw_ID.units = "DegC-week"
        dhw_ID.long_name = "degree heating week"
        dhw_ID.standard_name = "DHW"
        dhw_ID.missing_value = 1.0e35

        lon_ID[:] = nc_handles[0].variables['lon_reef'][:]
        lat_ID[:] = nc_handles[0].variables['lat_reef'][:]
        time_ID[:] = list(range(timeframe[0], timeframe[1] + 1))
        GBRMPA_ID[:] = nc_handles[0].variables['LABEL_ID'][:]
        unique_ID[:] = np.array(nc_handles[0].variables['UNIQUE_ID'][:]).astype("int").astype("str")
        location_ID[:] = np.array(nc_handles[0].variables['UNIQUE_ID'][:]).astype("int").astype("str")

        for (idx, nc_handle) in enumerate(nc_handles):
            dhw_ID[idx, :, :] = nc_handle.variables['dhw_max'][:, start_yr_idx:end_yr_idx + 1]

    return None

"""Return a permutation that reorders the first list to match the second."""
def reorder_location_perm(rme_order: list[str], canonical_order: list[str]) -> list[int]:
    rme_id_to_index = {id_val: i for i, id_val in enumerate(rme_order)}
    new_order_indices = [rme_id_to_index[id_val] for id_val in canonical_order]

    return new_order_indices

"""
    format_connectivity_file(filepath: str, reorder: list[int], unique_ids : list[str]) -> pd.Dataframe:

Add unique ids to columns and rows.
"""
def format_connectivity_file(
    filepath: str,
    reorder: list[int],
    unique_ids : list[str]
) -> pd.DataFrame:
    connectivity = pd.read_csv(filepath, header=None, comment='#')
    connectivity = connectivity.iloc[reorder, reorder]
    connectivity.index = unique_ids
    connectivity.columns = unique_ids

    return connectivity


def format_csv_dhw_model_group(
    csv_files: list[str],
    output_filepath: str,
    timeframe: tuple,
    canonical_ids: list[str]
) -> None:
    """
    Formats a group of CSV DHW files (representing one RCP/Scenario) into a NetCDF.

    Args:
        csv_files: List of paths to CSV files (one per GCM).
        output_filepath: Output NetCDF path.
        timeframe: (start_year, end_year) tuple.
        canonical_ids: List of location IDs in the desired order.
    """
    if not csv_files:
        return

    n_sims = len(csv_files)
    n_locs = len(canonical_ids)
    start_year, end_year = timeframe
    n_years = end_year - start_year + 1

    dhw_data = np.zeros((n_sims, n_locs, n_years))

    for i, csv_path in enumerate(csv_files):
        df = pd.read_csv(csv_path)

        df.set_index(df.columns[0], inplace=True)

        df = df.reindex(canonical_ids)


        try:
            cols_map = {int(c): c for c in df.columns if str(c).isdigit()}
        except ValueError:
            raise ValueError(f"CSV headers in {csv_path} do not appear to be years.")

        target_years = range(start_year, end_year + 1)
        missing_years = [y for y in target_years if y not in cols_map]
        if missing_years:
             raise ValueError(f"Years {missing_years} missing in {csv_path}")

        selected_cols = [cols_map[y] for y in target_years]

        subset = df[selected_cols].values

        dhw_data[i, :, :] = subset

    with netCDF4.Dataset(output_filepath, "w", format="NETCDF4") as nc_out:
        nc_out.createDimension("model", n_sims)
        nc_out.createDimension("locations", n_locs)
        nc_out.createDimension("timesteps", n_years)

        time_ID = nc_out.createVariable("timesteps", "i4", ("timesteps",))
        unique_ID = nc_out.createVariable("UNIQUE_ID", str, ("locations",))

        dhw_ID = nc_out.createVariable(
            "dhw", "f8", ("model", "locations", "timesteps")
        )

        time_ID.units = "year"

        dhw_ID.units = "DegC-week"
        dhw_ID.long_name = "degree heating week"
        dhw_ID.missing_value = 1.0e35

        time_ID[:] = list(range(start_year, end_year + 1))
        unique_ID[:] = np.array(canonical_ids).astype(str)

        dhw_ID[:] = dhw_data

    return None
