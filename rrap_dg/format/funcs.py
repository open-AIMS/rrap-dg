import netCDF4
import numpy as np
import pandas as pd
import os
import re

def extract_model_name(filepath: str) -> str:
    """Extract model name from filename."""
    filename = os.path.basename(filepath)
    # Search for _SSPxxx, _sspxxx, _xxx, or _historical (where xxx is digits)
    # The user specifies model name is before _ssp<ssp>, _<ssp>, or _historical
    match = re.search(r"_(?:SSP|ssp|historical)\d*|_\d{3}", filename)
    if match:
        name = filename[:match.start()]
    else:
        # Fallback: return filename without extension
        name = os.path.splitext(filename)[0]

    # Strip known prefix if present
    return name.replace("CoralSea_GBR_", "")

def validate_location_agreement(dhw_nc_handles: list) -> None:
    """Check that all netcdf files refer to the same locations."""
    unique_ids = dhw_nc_handles[0].variables['UNIQUE_ID'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(unique_ids == nc_handle.variables['UNIQUE_ID'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different location UNIQUE_IDs."
            )

    return None

def validate_lon_agreement(dhw_nc_handles: list) -> None:
    """Check that all netcdf files refer to the same longitudes."""
    lons = dhw_nc_handles[0].variables['lon_reef'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(lons == nc_handle.variables['lon_reef'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different latitude arrays."
            )

    return None

def validate_lat_agreement(dhw_nc_handles: list) -> None:
    """Check that all netcdf files refer to the same latitudes."""
    lats = dhw_nc_handles[0].variables['lat_reef'][:]

    for nc_handle in dhw_nc_handles[1:]:
        if not all(lats == nc_handle.variables['lat_reef'][:]):
            raise ValueError(
                f"DHW files {dhw_nc_handles[0].filepath()} and {nc_handle.filepath()}"
                " have different latitude arrays."
            )

    return None

def validate_time_agreement(dhw_nc_handles: list) -> None:
    """Check that all netcdf files refer to the same timesteps."""
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

def format_mcb_dhw_with_prepend(
    hist_fps: list[str],
    proj_fps: list[str],
    output_filepath: str,
    hist_timeframe: tuple,
    proj_timeframe: tuple,
    hist_var: str = "dhw_max_0",
    proj_var: str = "dhw_max_150"
):
    """
    Consolidates DHW files by prepending historical data (usually dhw_max_0)
    onto projection data (e.g. dhw_max_150).
    """
    import os
    import re

    # 1. Match models between hist and proj
    def get_model(fp):
        # Specific match for the filenames like:
        # CoralSea_GBR_ACCESS-CM2_historical_r1i1p1f1_dhw_1951-2014-reefs-MCB-Cairns-albedo-02.nc
        # Split by '_' and take the 3rd element
        return os.path.basename(fp).split("_")[2]

    hist_models = {get_model(f): f for f in hist_fps}
    proj_models = {get_model(f): f for f in proj_fps}
    
    # Common models
    common_models = sorted(list(set(hist_models.keys()) & set(proj_models.keys())))
    if not common_models:
        raise ValueError("No common models found between historical and projection sets.")

    n_sims = len(common_models)
    n_locs = 3806
    n_years = (proj_timeframe[1] - hist_timeframe[0] + 1)

    with netCDF4.Dataset(output_filepath, "w", format="NETCDF4") as nc_out:
        nc_out.createDimension("scenarios", n_sims)
        nc_out.createDimension("locations", n_locs)
        nc_out.createDimension("timesteps", n_years)

        lon_v = nc_out.createVariable("longitude", "f8", ("locations",))
        lat_v = nc_out.createVariable("latitude", "f8", ("locations",))
        time_v = nc_out.createVariable("timesteps", "i4", ("timesteps",))
        model_v = nc_out.createVariable("model_names", str, ("scenarios",))
        unique_id_v = nc_out.createVariable("UNIQUE_ID", str, ("locations",))
        location_id_v = nc_out.createVariable("locations", str, ("locations",))
        
        # Output as (scenarios, locations, timesteps) for ADRIA
        dhw_v = nc_out.createVariable(
            "dhw", "f4", ("scenarios", "locations", "timesteps"), 
            fill_value=1.0e35, zlib=True, complevel=4
        )

        time_v[:] = np.arange(hist_timeframe[0], proj_timeframe[1] + 1)
        model_v[:] = np.array(common_models, dtype=object)

        # Get metadata from first projection file
        with netCDF4.Dataset(proj_models[common_models[0]], 'r') as ds:
            ids = np.array(ds.variables['UNIQUE_ID'][:]).astype(int).astype(str)
            unique_id_v[:] = ids
            location_id_v[:] = ids
            lat_v[:] = ds.variables['lat_reef'][:]
            lon_v[:] = ds.variables['lon_reef'][:]

        # Fill Data
        for m_idx, model in enumerate(common_models):
            print(f"    Processing model: {model}")
            # Hist chunk
            with netCDF4.Dataset(hist_models[model], 'r') as ds_h:
                h_start, h_end = get_time_index(ds_h, hist_timeframe)
                h_chunk = ds_h.variables[hist_var][:, h_start : h_end + 1]
            
            # Proj chunk
            with netCDF4.Dataset(proj_models[model], 'r') as ds_p:
                p_start, p_end = get_time_index(ds_p, proj_timeframe)
                p_chunk = ds_p.variables[proj_var][:, p_start : p_end + 1]

            # Concat and save
            full_ts = np.concatenate([h_chunk, p_chunk], axis=1)
            dhw_v[m_idx, :, :] = full_ts

    return None

def format_single_rcp_dhw(
        dhw_nc_fps: list[str], output_filepath: str, timeframe: tuple, variable_name: str = "dhw_max"
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
        # ... (rest of dimension/variable setup) ...
        nc_out.createDimension("scenarios", n_sims)
        nc_out.createDimension("locations", n_locs)
        nc_out.createDimension("timesteps", n_years)

        lon_ID = nc_out.createVariable("longitude", "f8", ("locations",))
        lat_ID = nc_out.createVariable("latitude", "f8", ("locations",))
        time_ID = nc_out.createVariable("timesteps", "i4", ("timesteps",))
        GBRMPA_ID = nc_out.createVariable("GBRMPA_ID", str, ("locations",))
        unique_ID = nc_out.createVariable("UNIQUE_ID", str, ("locations",))
        location_ID = nc_out.createVariable("locations", str, ("locations",))
        model_name_ID = nc_out.createVariable("model_names", str, ("scenarios",))
        dhw_ID = nc_out.createVariable(
            "dhw", "f8", ("scenarios", "locations", "timesteps"), fill_value=1.0e35
        ) # Dimension order flipped to consistency with MATLAB/Julia

        lat_ID.units = "degrees_north"
        lat_ID.long_name = "latitude"
        lat_ID.standard_name = "latitude"

        lon_ID.units = "degrees_east"
        lon_ID.long_name = "longitude"
        lon_ID.standard_name = "longitude"

        time_ID.units = "year"
        time_ID.long_name = "timesteps"
        time_ID.standard_name = "timesteps"

        GBRMPA_ID.units = ""
        GBRMPA_ID.long_name = "gbrmpa id"

        unique_ID.units = ""
        unique_ID.long_name = "unique id"

        location_ID.units = ""
        location_ID.long_name = "unique id"

        model_name_ID.units = ""
        model_name_ID.long_name = "climate model name"

        dhw_ID.units = "DegC-week"
        dhw_ID.long_name = "degree heating week"

        lon_ID[:] = nc_handles[0].variables['lon_reef'][:]
        lat_ID[:] = nc_handles[0].variables['lat_reef'][:]
        time_ID[:] = list(range(timeframe[0], timeframe[1] + 1))
        GBRMPA_ID[:] = nc_handles[0].variables['LABEL_ID'][:]
        unique_ID[:] = np.array(nc_handles[0].variables['UNIQUE_ID'][:]).astype("int").astype("str")
        location_ID[:] = np.array(nc_handles[0].variables['UNIQUE_ID'][:]).astype("int").astype("str")
        model_name_ID[:] = np.array([extract_model_name(fp) for fp in dhw_nc_fps], dtype=object)

        for (idx, nc_handle) in enumerate(nc_handles):
            dhw_ID[idx, :, :] = nc_handle.variables[variable_name][:, start_yr_idx:end_yr_idx + 1]

    return None

def reorder_location_perm(rme_order: list[str], canonical_order: list[str]) -> list[int]:
    """Return a permutation that reorders the first list to match the second."""
    rme_id_to_index = {id_val: i for i, id_val in enumerate(rme_order)}
    new_order_indices = [rme_id_to_index[id_val] for id_val in canonical_order]

    return new_order_indices

def format_connectivity_file(
    filepath: str,
    reorder: list[int],
    unique_ids : list[str]
) -> pd.DataFrame:
    """Add unique ids to columns and rows."""
    connectivity = pd.read_csv(filepath, header=None, comment='#')
    connectivity = connectivity.iloc[reorder, reorder]
    connectivity.index = unique_ids
    connectivity.columns = unique_ids

    return connectivity


def format_csv_dhw_model_group(
    csv_files: list[str],
    output_filepath: str,
    timeframe: tuple,
    rme_gbrmpa_ids: list[str],
    unique_ids: list[str]
) -> None:
    """
    Formats a group of CSV DHW files (representing one RCP/Scenario) into a NetCDF.

    Args:
        csv_files: List of paths to CSV files (one per GCM).
        output_filepath: Output NetCDF path.
        timeframe: (start_year, end_year) tuple.
        unique_ids: List of location IDs in the desired order.
    """
    if not csv_files:
        return

    n_sims = len(csv_files)
    n_locs = len(unique_ids)
    start_year, end_year = timeframe
    n_years = end_year - start_year + 1

    dhw_data = np.zeros((n_sims, n_locs, n_years))
    rme_gbrmpa_idx = pd.Index(rme_gbrmpa_ids)
    unique_idx = pd.Index(unique_ids)

    for i, csv_path in enumerate(csv_files):
        df = pd.read_csv(csv_path)

        df.set_index(df.columns[0], inplace=True)
        df_idx = pd.Index(df.index)
        if set(rme_gbrmpa_idx) != set(df_idx):
            raise ValueError(f"IDs in {csv_path} do not align with canonical GBRMPA IDs")

        df = df.reindex(rme_gbrmpa_idx)
        df.index = unique_idx


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

    print("here")
    with netCDF4.Dataset(output_filepath, "w", format="NETCDF4") as nc_out:
        nc_out.createDimension("scenarios", n_sims)
        nc_out.createDimension("locations", n_locs)
        nc_out.createDimension("timesteps", n_years)

        time_ID = nc_out.createVariable("timesteps", "i4", ("timesteps",))
        unique_ID = nc_out.createVariable("UNIQUE_ID", str, ("locations",))
        model_name_ID = nc_out.createVariable("model_names", str, ("scenarios",))
        location_ID = nc_out.createVariable("locations", str, ("locations",))

        dhw_ID = nc_out.createVariable(
            "dhw", "f8", ("scenarios", "locations", "timesteps")
        )

        time_ID.units = "year"
        model_name_ID.long_name = "climate model name"
        model_name_ID.units = ""

        dhw_ID.units = "DegC-week"
        dhw_ID.long_name = "degree heating week"
        dhw_ID.missing_value = 1.0e35

        location_ID.units = ""
        location_ID.long_name = "unique id"

        time_ID[:] = list(range(start_year, end_year + 1))
        unique_ID[:] = np.array(unique_ids).astype(str)
        location_ID[:] = np.array(unique_ids).astype(str)
        model_name_ID[:] = np.array([extract_model_name(fp) for fp in csv_files], dtype=object)

        dhw_ID[:] = dhw_data

    return None

def format_5d_mcb_dhw(
    input_dir: str,
    output_filepath: str,
    region: str,
    ssp: str,
    hist_timeframe: tuple = (2007, 2014),
    proj_timeframe: tuple = (2015, 2100)
):
    """
    Consolidates raw MCB NetCDF files for a specific SSP into a 5D NetCDF,
    prepending historical data (2007-2014) with MCB to projections (2015-2100).
    
    Dimensions: (albedo, mcb_durations, scenarios, locations, timesteps)
    """
    import glob
    import os
    
    albedo_subdirs = ["Albedo_0.2", "Albedo_0.3"]
    albedo_vals = [0.2, 0.3]
    mcb_durations = [0, 50, 100, 150]
    mcb_vars = ["dhw_max_0", "dhw_max_50", "dhw_max_100", "dhw_max_150"]
    
    # 1. Collect all projection files for the region and specific SSP
    proj_files = []
    for alb_sub in albedo_subdirs:
        alb_val = float(alb_sub.split("_")[1])
        pattern = os.path.join(input_dir, region, alb_sub, "Projections", f"*{ssp}*.nc")
        fps = glob.glob(pattern)
        for fp in fps:
            with netCDF4.Dataset(fp, 'r') as ds:
                model = getattr(ds, 'parent_source_id', "unknown")
            proj_files.append({
                'path': fp,
                'albedo': alb_val,
                'model': model
            })

    # 2. Collect historical files for the same region
    hist_files = []
    for alb_sub in albedo_subdirs:
        alb_val = float(alb_sub.split("_")[1])
        pattern = os.path.join(input_dir, region, alb_sub, "Historical", "*.nc")
        fps = glob.glob(pattern)
        for fp in fps:
            with netCDF4.Dataset(fp, 'r') as ds:
                model = getattr(ds, 'parent_source_id', "unknown")
            hist_files.append({
                'path': fp,
                'albedo': alb_val,
                'model': model
            })
            
    # Identify unique Models common to all albedo/hist/proj sets
    models_per_alb = {}
    for alb in albedo_vals:
        p_models = {f['model'] for f in proj_files if f['albedo'] == alb}
        h_models = {f['model'] for f in hist_files if f['albedo'] == alb}
        models_per_alb[alb] = p_models & h_models
    
    models = sorted(list(set.intersection(*models_per_alb.values())))
    if not models:
        raise ValueError(f"No common models found for region {region} and SSP {ssp}")

    n_scenarios = len(models)
    n_mcb = len(mcb_durations)
    n_albedo = len(albedo_vals)
    n_locs = 3806
    n_years = (proj_timeframe[1] - hist_timeframe[0] + 1)
    
    # 3. Create output NetCDF
    with netCDF4.Dataset(output_filepath, "w", format="NETCDF4") as nc_out:
        nc_out.createDimension("albedo", n_albedo)
        nc_out.createDimension("mcb_durations", n_mcb)
        nc_out.createDimension("scenarios", n_scenarios)
        nc_out.createDimension("locations", n_locs)
        nc_out.createDimension("timesteps", n_years)
        
        # Variables
        time_v = nc_out.createVariable("timesteps", "i4", ("timesteps",))
        unique_id_v = nc_out.createVariable("UNIQUE_ID", str, ("locations",))
        location_id_v = nc_out.createVariable("locations", str, ("locations",))
        lat_v = nc_out.createVariable("latitude", "f8", ("locations",))
        lon_v = nc_out.createVariable("longitude", "f8", ("locations",))
        model_v = nc_out.createVariable("model_names", str, ("scenarios",))
        mcb_v = nc_out.createVariable("mcb_durations", "i4", ("mcb_durations",))
        albedo_v = nc_out.createVariable("albedo", "f4", ("albedo",))
        
        # 5D DHW variable - Reordered to (albedo, mcb_durations, scenarios, locations, timesteps)
        dhw_v = nc_out.createVariable(
            "dhw", "f4", ("albedo", "mcb_durations", "scenarios", "locations", "timesteps"),
            fill_value=1.0e35,
            zlib=True, complevel=4
        )
        
        # Attributes
        time_v.units = "year"
        mcb_v.units = "days"
        albedo_v.units = "fraction"
        dhw_v.units = "DegC-week"
        lat_v.units = "degrees_north"
        lon_v.units = "degrees_east"
        
        # Fill coords
        time_v[:] = np.arange(hist_timeframe[0], proj_timeframe[1] + 1)
        mcb_v[:] = np.array(mcb_durations)
        albedo_v[:] = np.array(albedo_vals)
        model_v[:] = np.array(models, dtype=object)
        
        # Load one file to get static reef data
        with netCDF4.Dataset(proj_files[0]['path'], 'r') as ds:
            ids = np.array(ds.variables['UNIQUE_ID'][:]).astype(int).astype(str)
            unique_id_v[:] = ids
            location_id_v[:] = ids
            lat_v[:] = ds.variables['lat_reef'][:]
            lon_v[:] = ds.variables['lon_reef'][:]

        # Helper to find file path
        def find_fp(file_list, model, albedo):
            for f in file_list:
                if f['model'] == model and f['albedo'] == albedo:
                    return f['path']
            return None

        # 4. Fill Data
        for alb_idx, alb_val in enumerate(albedo_vals):
            for scen_idx, model in enumerate(models):
                p_fp = find_fp(proj_files, model, alb_val)
                h_fp = find_fp(hist_files, model, alb_val)
                
                print(f"  Consolidating {region} | {ssp} | Albedo {alb_val} | {model} (with prepend)")
                with netCDF4.Dataset(h_fp, 'r') as ds_h, netCDF4.Dataset(p_fp, 'r') as ds_p:
                    h_start, h_end = get_time_index(ds_h, hist_timeframe)
                    p_start, p_end = get_time_index(ds_p, proj_timeframe)
                    
                    for mcb_idx, mcb_var in enumerate(mcb_vars):
                        h_chunk = ds_h.variables[mcb_var][:, h_start : h_end + 1]
                        p_chunk = ds_p.variables[mcb_var][:, p_start : p_end + 1]
                        
                        # Concatenate and save to 5D: (albedo, mcb_durations, scenarios, locations, timesteps)
                        dhw_v[alb_idx, mcb_idx, scen_idx, :, :] = np.concatenate([h_chunk, p_chunk], axis=1)

    return None

    return None
