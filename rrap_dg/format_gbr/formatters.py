from abc import ABC, abstractmethod
from typing import Dict, Any
import os
import shutil
from glob import glob
from os.path import join as pj, basename
import pandas as pd
import geopandas as gpd
import re
from itertools import groupby

from .exceptions import ConfigurationError
from .format_funcs import format_connectivity_file, reorder_location_perm, format_single_rcp_dhw, format_csv_dhw_model_group

# Import juliacall and set up Julia environment once
import juliacall
from rrap_dg import PKG_PATH
jl_icc = juliacall.newmodule("DownscaleInitialCoralCover")
jl_icc.seval(f'include("{PKG_PATH}/initial_coral_cover/icc.jl")')


class Formatter(ABC):
    """Abstract base class for data formatters."""
    
    description: str = "Generic formatter"

    @abstractmethod
    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        """
        Format the data from source_path and write to output_path.
        
        Args:
            source_path: Resolved local path to the source data.
            output_path: Full path where the output file should be written.
            options: Dictionary of specific options for this formatter.
            source_manager: Instance of SourceManager to resolve auxiliary sources.
        """
        pass

def _find_rme_root(source_path: str) -> str:
    """
    Finds the root directory of a ReefMod Engine dataset.
    It looks for the directory containing the 'data_files' subdirectory.
    """
    # Check if we are already at the root containing data_files
    if os.path.isdir(pj(source_path, "data_files")):
        return source_path
    
    # Check if we are pointing directly to data_files
    if basename(source_path) == "data_files" and os.path.isdir(source_path):
        return os.path.dirname(source_path)
        
    # Recursive search for data_files directory
    found = glob(pj(source_path, "**", "data_files"), recursive=True)
    # Filter to ensure we only get directories
    found_dirs = [f for f in found if os.path.isdir(f)]
    
    if found_dirs:
        # Use the first one found. found_dirs[0] is path/to/data_files
        # We want the parent of data_files
        return os.path.dirname(found_dirs[0])
        
    raise RuntimeError(f"Could not find 'data_files' directory in {source_path} or its subdirectories.")

class RMEConnectivityFormatter(Formatter):
    """
    Formats connectivity data from ReefMod Engine output.
    Requires a secondary 'spatial_source' option for the canonical geopackage.
    """
    description = "Transforms ReefMod Engine connectivity CSVs (headerless) into a labeled CSV format, aligning locations with the canonical domain IDs."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        spatial_source_key = options.get("spatial_source")
        if not spatial_source_key:
            raise ConfigurationError("RMEConnectivityFormatter requires 'spatial_source' in options.")
        
        spatial_path = source_manager.resolve_source_path(spatial_source_key)
        
        # Finding the geopackage file
        if os.path.isdir(spatial_path):
            gpkg_files = glob(pj(spatial_path, "*.gpkg"))
            if not gpkg_files:
                raise RuntimeError(f"No .gpkg file found in spatial source: {spatial_path}")
            canonical_gpkg_path = gpkg_files[0]
        else:
            canonical_gpkg_path = spatial_path

        # Resolve RME data root using helper
        rme_root_path = _find_rme_root(source_path)
        rme_data_path = pj(rme_root_path, "data_files")

        connectivity_pattern = pj(rme_data_path, "con_csv", "CONNECT_ACRO*.csv")
        connectivity_files = glob(connectivity_pattern)
        
        if not connectivity_files:
             raise RuntimeError(f"No connectivity CSVs found in {connectivity_pattern}")

        # ID list
        rme_id_list_path = pj(rme_data_path, "id", "id_list_*.csv")
        rme_id_files = glob(rme_id_list_path)
        if not rme_id_files:
            raise RuntimeError(f"No ID list found in {rme_id_list_path}")
        
        rme_ids = pd.read_csv(rme_id_files[0], comment="#", header=None)
        canonical = gpd.read_file(canonical_gpkg_path)

        # Calculate permutation
        reorder_perm = reorder_location_perm(rme_ids[0], canonical.RME_GBRMPA_ID)
        
        if not os.path.splitext(output_path)[1]:
            # It's a directory
            os.makedirs(output_path, exist_ok=True)
            for con_fn in connectivity_files:
                fname = basename(con_fn)
                out_fn = pj(output_path, fname)
                con_df = format_connectivity_file(con_fn, reorder_perm, canonical["UNIQUE_ID"])
                con_df.to_csv(out_fn)
        else:
            if len(connectivity_files) > 1:
                print(f"Warning: Multiple connectivity files found but single output file specified. Using first one: {connectivity_files[0]}")
            
            con_df = format_connectivity_file(connectivity_files[0], reorder_perm, canonical["UNIQUE_ID"])
            con_df.to_csv(output_path)

class DHWFormatter(Formatter):
    """
    Formats Degree Heating Week (DHW) NetCDF files.
    """
    description = "Standardizes Degree Heating Week (DHW) NetCDF files into the project's expected structure and naming convention."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        rcps_opt = options.get("rcps", "2.6 4.5 7.0 8.5")
        timeframe_opt = options.get("timeframe", "2025 2099")
        
        # Parse options
        _timeframe = tuple(map(int, timeframe_opt.split(" ")))
        rcps_tuple = tuple(rcps_opt.split(" "))
        
        rcps_to_ssps = {"2.6": "ssp126", "4.5": "ssp245", "7.0": "ssp370", "8.5": "ssp585"}
        rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}

        format_rcps = [rcps_fn[rcp] for rcp in rcps_tuple]
        ssps = [rcps_to_ssps[rcp] for rcp in rcps_tuple]
        
        # Search for files
        search_paths = [pj(source_path, f"*{ssp}*") for ssp in ssps]
        netcdf_files = [sorted(glob(search_path)) for search_path in search_paths]
        
        # Ensure output directory exists (since we generate multiple files)
        os.makedirs(output_path, exist_ok=True)
        
        output_fps = [pj(output_path, f"dhwRCP{rcp}.nc") for rcp in format_rcps]

        for (src_files, out_fp) in zip(netcdf_files, output_fps):
            if not src_files:
                print(f"Warning: No source files found for RCP corresponding to {out_fp}")
                continue
            format_single_rcp_dhw(src_files, out_fp, _timeframe)
            
        # Optional: Update README with GCM info
        domain_dir = os.path.dirname(output_path)
        readme_path = pj(domain_dir, "README.md")
        
        if os.path.exists(readme_path) and netcdf_files and netcdf_files[0]:
            self._update_readme(readme_path, netcdf_files[0])

    def _update_readme(self, readme_path: str, first_rcp_files: list):
        gcms_list = []
        for fp in first_rcp_files:
            filename = basename(fp)
            parts = filename.split("_")
            if len(parts) > 2:
                gcms_list.append(parts[2])
            else:
                gcms_list.append("Unknown")
        
        grouped_gcms = [(key, len(list(group))) for key, group in groupby(gcms_list)]

        with open(readme_path, "a") as f:
            f.write("\n\n## DHW Climate Models\n\n")
            f.write("The `model` dimension in the DHW NetCDF files corresponds to the following climate models (indices are 1-based):\n\n")
            
            current_idx = 1
            for gcm, count in grouped_gcms:
                end_idx = current_idx + count - 1
                if count > 1:
                    f.write(f"*   {gcm} ({current_idx}:{end_idx})\n")
                else:
                    f.write(f"*   {gcm} ({current_idx})\n")
                current_idx += count

class RMEDHWFormatter(Formatter):
    """
    Formats DHW data provided as CSVs (one per GCM) in the RME data structure.
    Requires 'spatial_source' to align with canonical IDs.
    """
    description = "Converts ReefMod Engine CSV-based DHW projections (one file per GCM) into standardized NetCDF files."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        spatial_source_key = options.get("spatial_source")
        if not spatial_source_key:
            raise ConfigurationError("RMEDHWFormatter requires 'spatial_source' in options.")
        
        spatial_path = source_manager.resolve_source_path(spatial_source_key)
        
        # Get canonical IDs and coordinates
        if os.path.isdir(spatial_path):
            gpkg_files = glob(pj(spatial_path, "*.gpkg"))
            if not gpkg_files:
                raise RuntimeError(f"No .gpkg file found in spatial source: {spatial_path}")
            canonical_gpkg_path = gpkg_files[0]
        else:
            canonical_gpkg_path = spatial_path
            
        gdf = gpd.read_file(canonical_gpkg_path)
        canonical_ids = gdf["UNIQUE_ID"].tolist()
        lons = gdf.geometry.centroid.x.values
        lats = gdf.geometry.centroid.y.values

        # Resolve RME data root and find dhw_csv
        rme_root_path = _find_rme_root(source_path)
        dhw_csv_dir = pj(rme_root_path, "data_files", "dhw_csv")
        
        if not os.path.isdir(dhw_csv_dir):
            if basename(source_path) == "dhw_csv":
                dhw_csv_dir = source_path
            else:
                 raise RuntimeError(f"Could not find 'dhw_csv' directory in {rme_root_path}")

        # Parse options
        rcps_opt = options.get("rcps", "2.6 4.5 7.0 8.5")
        timeframe_opt = options.get("timeframe", "2025 2099")
        _timeframe = tuple(map(int, timeframe_opt.split(" ")))
        
        rcps_tuple = tuple(rcps_opt.split(" "))
        rcps_to_ssp_patterns = {
            "2.6": ["126", "SSP126"], 
            "4.5": ["245", "SSP245"], 
            "7.0": ["370", "SSP370"], 
            "8.5": ["585", "SSP585"]
        }
        rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}

        os.makedirs(output_path, exist_ok=True)
        
        # Keep track of files for one RCP to update README
        example_rcp_files = None
        
        for rcp in rcps_tuple:
            patterns = rcps_to_ssp_patterns.get(rcp, [])
            all_csvs = glob(pj(dhw_csv_dir, "*.csv"))
            
            rcp_files = []
            for f in all_csvs:
                fname = basename(f)
                if any(pat in fname for pat in patterns):
                    rcp_files.append(f)
            
            rcp_files = sorted(list(set(rcp_files)))
            
            if not rcp_files:
                print(f"Warning: No CSV files found for RCP {rcp} in {dhw_csv_dir}")
                continue
            
            if example_rcp_files is None:
                example_rcp_files = rcp_files
                
            out_fp = pj(output_path, f"dhwRCP{rcps_fn[rcp]}.nc")
            print(f"Formatting {len(rcp_files)} CSVs for RCP {rcp} to {out_fp}...")
            
            format_csv_dhw_model_group(
                rcp_files, 
                out_fp, 
                _timeframe, 
                canonical_ids, 
                lats, 
                lons
            )

        # Update README with model info
        domain_dir = os.path.dirname(output_path)
        readme_path = pj(domain_dir, "README.md")
        if os.path.exists(readme_path) and example_rcp_files:
            self._update_readme(readme_path, example_rcp_files)

    def _update_readme(self, readme_path: str, files: list):
        gcms_list = []
        for fp in files:
            filename = basename(fp)
            # Regex to extract model name before the scenario part (e.g. SSP126, 126, 370)
            # Matches anything up to the underscore before (SSP)?\d{3}
            match = re.search(r"^(.*?)_(?:SSP)?\d{3}", filename)
            if match:
                gcms_list.append(match.group(1))
            else:
                gcms_list.append(filename) # Fallback

        grouped_gcms = [(key, len(list(group))) for key, group in groupby(gcms_list)]

        with open(readme_path, "a") as f:
            f.write("\n\n## DHW Climate Models (RME Source)\n\n")
            f.write("The `model` dimension in the DHW NetCDF files corresponds to the following climate models (indices are 1-based):\n\n")
            
            current_idx = 1
            for gcm, count in grouped_gcms:
                end_idx = current_idx + count - 1
                if count > 1:
                    f.write(f"*   {gcm} ({current_idx}:{end_idx})\n")
                else:
                    f.write(f"*   {gcm} ({current_idx})\n")
                current_idx += count

class GBRICCFormatter(Formatter):
    """
    Formats Initial Coral Cover (ICC) data for the GBR by calling Julia functions.
    Requires a secondary 'canonical_source' option for the canonical geopackage.
    """
    description = "Aggregates ReefMod Engine Initial Coral Cover (ICC) CSVs by averaging over repeats, converting percentages to proportions, and aligning with the canonical domain IDs, then saving as a NetCDF."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        canonical_source_key = options.get("canonical_source")
        if not canonical_source_key:
            raise ConfigurationError("GBRICCFormatter requires 'canonical_source' in options.")
        
        canonical_path = source_manager.resolve_source_path(canonical_source_key)

        # Finding the geopackage file
        if os.path.isdir(canonical_path):
            gpkg_files = glob(pj(canonical_path, "*.gpkg"))
            if not gpkg_files:
                raise RuntimeError(f"No .gpkg file found in canonical source: {canonical_path}")
            canonical_gpkg_path = gpkg_files[0]
        else:
            canonical_gpkg_path = canonical_path
        
        # Resolve RME data root using helper to ensure Julia gets the path containing 'data_files'
        rme_root_path = _find_rme_root(source_path)

        # Call the Julia function
        print(f"Calling Julia format_rme_icc with rme_path={rme_root_path}, canonical_path={canonical_gpkg_path}, output_path={output_path}")
        jl_icc.format_rme_icc(rme_root_path, canonical_gpkg_path, output_path)

class MoveFileFormatter(Formatter):
    """
    A generic formatter to move a specified file or a file matching a pattern
    from the source_path to the output_path.
    Expects 'filename_or_pattern' in options.
    """
    description = "Copies a specific file or files matching a pattern from the source to the destination."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        filename_or_pattern = options.get("filename_or_pattern")
        if not filename_or_pattern:
            raise ConfigurationError("MoveFileFormatter requires 'filename_or_pattern' in options.")

        full_source_pattern = pj(source_path, filename_or_pattern)
        found_files = glob(full_source_pattern)
        
        if not found_files:
            raise RuntimeError(f"No files found matching pattern '{filename_or_pattern}' in source: {source_path}")
        
        if len(found_files) > 1:
            raise RuntimeError(f"Multiple files found for pattern '{filename_or_pattern}' in source: {source_path}. "
                               f"Please specify a more precise pattern or a single filename. Found: {found_files}")

        src_file_path = found_files[0]
        
        if not os.path.exists(src_file_path):
            raise RuntimeError(f"Source file not found: {src_file_path}")
            
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        print(f"Moving file from {src_file_path} to {output_path}")
        shutil.copyfile(src_file_path, output_path)


class FormatterRegistry:
    _formatters = {
        "rme_connectivity": RMEConnectivityFormatter,
        "standard_netcdf_dhw": DHWFormatter,
        "rme_dhw": RMEDHWFormatter,
        "gbr_icc": GBRICCFormatter,
        "move_file_formatter": MoveFileFormatter,
    }

    @classmethod
    def get(cls, name: str) -> Formatter:
        if name not in cls._formatters:
            raise ValueError(f"Unknown formatter: {name}")
        return cls._formatters[name]()
