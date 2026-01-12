from typing import List, Tuple, Dict
from pydantic import BaseModel, Field

class BaseFormatterOptions(BaseModel):
    pass

class RMEConnectivityOptions(BaseFormatterOptions):
    spatial_source: str = Field(..., description="Key of the spatial source in configuration.")
    # Patterns for extraction
    gpkg_pattern: str = Field("*.gpkg", description="Pattern to find the geopackage in the spatial source directory.")
    connectivity_pattern: str = Field("**/data_files/con_csv/CONNECT_ACRO*.csv", description="Glob pattern to find connectivity CSVs relative to source root.")
    id_list_pattern: str = Field("**/data_files/id/id_list_*.csv", description="Glob pattern to find ID list CSV relative to source root.")

class DHWOptions(BaseFormatterOptions):
    rcps: str = Field("2.6 4.5 7.0 8.5", description="Space-separated list of RCPs.")
    timeframe: str = Field("2025 2099", description="Space-separated start and end years.")

    # Logic configuration
    rcp_ssp_map: Dict[str, str] = Field(
        default={
            "2.6": "ssp126",
            "4.5": "ssp245",
            "7.0": "ssp370",
            "8.5": "ssp585"
        },
        description="Mapping from RCP values to SSP filename substrings."
    )
    filename_template: str = Field("*{ssp}*", description="Glob template for finding files. {ssp} will be replaced by the value from rcp_ssp_map.")

    @property
    def rcp_list(self) -> List[str]:
        return self.rcps.split(" ")

    @property
    def timeframe_tuple(self) -> Tuple[int, int]:
        try:
            parts = list(map(int, self.timeframe.split(" ")))
            if len(parts) != 2:
                raise ValueError
            return (parts[0], parts[1])
        except ValueError:
            raise ValueError(f"Invalid timeframe format: '{self.timeframe}'. Expected 'YYYY YYYY'.")

class RMEDHWOptions(DHWOptions):
    spatial_source: str = Field(..., description="Key of the spatial source to align with.")
    gpkg_pattern: str = Field("*.gpkg", description="Pattern to find the geopackage in the spatial source directory.")
    dhw_csv_pattern: str = Field("**/data_files/dhw_csv/*.csv", description="Glob pattern to find DHW CSVs.")

    # Mapping for CSV filename matching
    # Note: RME CSVs often use '126', 'SSP126' patterns.
    # We will use a list of match strings for each RCP.
    rcp_match_patterns: Dict[str, List[str]] = Field(
        default={
            "2.6": ["126", "SSP126"],
            "4.5": ["245", "SSP245"],
            "7.0": ["370", "SSP370"],
            "8.5": ["585", "SSP585"]
        },
        description="List of substrings to match in filenames for each RCP."
    )

class GBRICCOptions(BaseFormatterOptions):
    canonical_source: str = Field(..., description="Key of the canonical spatial source.")
    gpkg_pattern: str = Field("*.gpkg", description="Pattern to find the geopackage in the canonical source directory.")

class MoveFileOptions(BaseFormatterOptions):
    filename_or_pattern: str = Field(..., description="Filename or glob pattern to match in source.")
