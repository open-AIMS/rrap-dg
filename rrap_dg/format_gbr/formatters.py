import os
import shutil
import pandas as pd
import geopandas as gpd
from abc import ABC, abstractmethod
from typing import Dict, Any
from glob import glob
from os.path import join as pj, basename

from .exceptions import ConfigurationError
from .format_funcs import format_connectivity_file, reorder_location_perm, format_single_rcp_dhw, format_csv_dhw_model_group
from .models import (
    RMEConnectivityOptions,
    DHWOptions,
    RMEDHWOptions,
    GBRICCOptions,
    MoveFileOptions
)

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
    if os.path.isdir(pj(source_path, "data_files")):
        return source_path

    if basename(source_path) == "data_files" and os.path.isdir(source_path):
        return os.path.dirname(source_path)

    found = glob(pj(source_path, "**", "data_files"), recursive=True)
    found_dirs = [f for f in found if os.path.isdir(f)]

    if found_dirs:

        return os.path.dirname(found_dirs[0])

    raise FileNotFoundError("Unable to identify RME directory structure.")

class RMEConnectivityFormatter(Formatter):
    """
    Formats connectivity data from ReefMod Engine output.
    Requires a secondary 'spatial_source' option for the canonical geopackage.
    """
    description = "Transforms ReefMod Engine connectivity CSVs (headerless) into a labeled CSV format, aligning locations with the canonical domain IDs."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        opts = RMEConnectivityOptions(**options)

        spatial_path = source_manager.resolve_source_path(opts.spatial_source)

        # Finding the geopackage file using pattern
        if os.path.isdir(spatial_path):
            gpkg_files = glob(pj(spatial_path, opts.gpkg_pattern))
            if not gpkg_files:
                raise RuntimeError(f"No file matching '{opts.gpkg_pattern}' found in spatial source: {spatial_path}")
            canonical_gpkg_path = gpkg_files[0]
        else:
            canonical_gpkg_path = spatial_path

        connectivity_files = glob(pj(source_path, opts.connectivity_pattern), recursive=True)

        if not connectivity_files:
             raise RuntimeError(f"No connectivity CSVs found matching '{opts.connectivity_pattern}' in {source_path}")

        # Find ID list using recursive glob pattern
        rme_id_files = glob(pj(source_path, opts.id_list_pattern), recursive=True)
        if not rme_id_files:
            raise RuntimeError(f"No ID list found matching '{opts.id_list_pattern}' in {source_path}")

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
        opts = DHWOptions(**options)

        _timeframe = opts.timeframe_tuple
        rcps_list = opts.rcp_list

        rcps_to_ssps = opts.rcp_ssp_map
        rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}

        format_rcps = []
        ssps = []
        for rcp in rcps_list:
            if rcp not in rcps_to_ssps:
                 print(f"Warning: RCP {rcp} not found in rcp_ssp_map. Skipping.")
                 continue
            format_rcps.append(rcps_fn.get(rcp, rcp.replace(".", "")))
            ssps.append(rcps_to_ssps[rcp])

        search_paths = [pj(source_path, opts.filename_template.format(ssp=ssp)) for ssp in ssps]
        netcdf_files = [sorted(glob(search_path)) for search_path in search_paths]

        os.makedirs(output_path, exist_ok=True)
        output_fps = [pj(output_path, f"dhwRCP{rcp}.nc") for rcp in format_rcps]

        for (src_files, out_fp) in zip(netcdf_files, output_fps):
            if not src_files:
                print(f"Warning: No source files found for RCP corresponding to {out_fp}")
                continue
            format_single_rcp_dhw(src_files, out_fp, _timeframe)

class RMEDHWFormatter(Formatter):
    """
    Formats DHW data provided as CSVs (one per GCM) in the RME data structure.
    Requires 'spatial_source' to align with canonical IDs.
    """
    description = "Converts ReefMod Engine CSV-based DHW projections (one file per GCM) into standardized NetCDF files."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        opts = RMEDHWOptions(**options)

        spatial_path = source_manager.resolve_source_path(opts.spatial_source)

        # Get canonical IDs and coordinates
        if os.path.isdir(spatial_path):
            gpkg_files = glob(pj(spatial_path, opts.gpkg_pattern))
            if not gpkg_files:
                raise RuntimeError(f"No file matching '{opts.gpkg_pattern}' found in spatial source: {spatial_path}")
            canonical_gpkg_path = gpkg_files[0]
        else:
            canonical_gpkg_path = spatial_path

        gdf = gpd.read_file(canonical_gpkg_path)
        canonical_ids = gdf["UNIQUE_ID"].tolist()

        _timeframe = opts.timeframe_tuple
        rcps_list = opts.rcp_list
        rcps_to_ssp_patterns = opts.rcp_match_patterns
        rcps_fn = {"2.6": "26", "4.5": "45", "7.0": "70", "8.5": "85"}

        os.makedirs(output_path, exist_ok=True)

        all_csvs = glob(pj(source_path, opts.dhw_csv_pattern), recursive=True)

        if not all_csvs:
            print(f"Warning: No CSV files found matching '{opts.dhw_csv_pattern}' in {source_path}")

        for rcp in rcps_list:
            patterns = rcps_to_ssp_patterns.get(rcp, [])

            rcp_files = []
            for f in all_csvs:
                fname = basename(f)
                if any(pat in fname for pat in patterns):
                    rcp_files.append(f)

            rcp_files = sorted(list(set(rcp_files)))

            if not rcp_files:
                print(f"Warning: No CSV files found for RCP {rcp} in {source_path}")
                continue

            out_fp = pj(output_path, f"dhwRCP{rcps_fn.get(rcp, rcp.replace('.', ''))}.nc")
            print(f"Formatting {len(rcp_files)} CSVs for RCP {rcp} to {out_fp}...")

            format_csv_dhw_model_group(
                rcp_files,
                out_fp,
                _timeframe,
                canonical_ids
            )

class GBRICCFormatter(Formatter):
    """
    Formats Initial Coral Cover (ICC) data for the GBR by calling Julia functions.
    Requires a secondary 'canonical_source' option for the canonical geopackage.
    """
    description = "Aggregates ReefMod Engine Initial Coral Cover (ICC) CSVs by averaging over repeats, converting percentages to proportions, and aligning with the canonical domain IDs, then saving as a NetCDF."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        opts = GBRICCOptions(**options)

        canonical_path = source_manager.resolve_source_path(opts.canonical_source)

        # Finding the geopackage file
        if os.path.isdir(canonical_path):
            gpkg_files = glob(pj(canonical_path, opts.gpkg_pattern))
            if not gpkg_files:
                raise RuntimeError(f"No file matching '{opts.gpkg_pattern}' found in canonical source: {canonical_path}")
            canonical_gpkg_path = gpkg_files[0]
        else:
            canonical_gpkg_path = canonical_path

        rme_root_path = _find_rme_root(source_path)

        jl_icc.format_rme_icc(rme_root_path, canonical_gpkg_path, output_path)

class MoveFileFormatter(Formatter):
    """
    A generic formatter to move a specified file or a file matching a pattern
    from the source_path to the output_path.
    Expects 'filename_or_pattern' in options.
    """
    description = "Copies a specific file or files matching a pattern from the source to the destination."

    def format(self, source_path: str, output_path: str, options: Dict[str, Any], source_manager) -> None:
        opts = MoveFileOptions(**options)

        filename_or_pattern = opts.filename_or_pattern

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
