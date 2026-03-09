import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rrap_dg.datapackage import DataPackage, Resource, Source, Contributor, SimulationMetadata
from rrap_dg.utils import extract_metadata, is_handle_id
from rrap_dg.__about__ import DATAPACKAGE_VERSION

# --- Constants for Hardcoded Metadata Information ---
DEFAULT_DATASET_NAME = "Unknown Dataset"
DEFAULT_CONTRIBUTOR_ROLE = "author"
DEFAULT_TIMEFRAME = [2025, 2099]
DEFAULT_DESCRIPTION = "Generated ADRIA Domain"

METADATA_FALLBACKS = ["datapackage.json", "metadata.json", "ro-crate-metadata.json"]

def _parse_as_datapackage(data: dict, original_source: str) -> Tuple[List[Source], List[Contributor]]:
    """Parses a dictionary following the standard datapackage structure."""
    sources = []
    is_handle = is_handle_id(original_source)
    
    for s in data.get("sources", []):
        source_obj = Source(**s)
        
        # If the original source for this resource is a handle, 
        # and this source entry's path is the same as our download dir (or handle is generic),
        # we can update it to be more accurate.
        if is_handle:
            # Only override if the current handle is empty or generic 'input'
            if not source_obj.handle or source_obj.handle == "input":
                source_obj.handle = original_source
                source_obj.path = ""
        else:
            # If it's a local path, ensure path is set and handle is blank (unless it already had one)
            if not source_obj.path:
                source_obj.path = original_source
        
        sources.append(source_obj)
        
    contributors = [Contributor(**c) for c in data.get("contributors", [])]
    return sources, contributors

def _parse_as_custom_metadata(data: dict, original_source: str) -> Tuple[List[Source], List[Contributor]]:
    """Parses a dictionary following a custom ADRIA/DataStore metadata structure."""
    info = data.get("dataset_info", {})
    associations = data.get("associations", {})
    
    title = info.get("name", data.get("name", DEFAULT_DATASET_NAME))
    desc = info.get("description", data.get("description", ""))
    contact = associations.get("point_of_contact")
    created = info.get("created_date", {}).get("value")
    published = info.get("published_date", {}).get("value")

    # If it's a handle, path should be blank. If local, it should be the original source.
    is_handle = is_handle_id(original_source)
    source_path = "" if is_handle else original_source
    source_handle = original_source if is_handle else ""

    source = Source(
        title=title, 
        description=desc, 
        path=source_path, 
        handle=source_handle,
        created_date=created, 
        published_date=published
    )
    
    contributors = []
    if contact:
        contributors.append(Contributor(
            title=contact.split("@")[0], 
            email=contact, 
            role=DEFAULT_CONTRIBUTOR_ROLE, 
            datasets=[title]
        ))
        
    return [source], contributors

def _load_and_parse_metadata(file_path: Path, original_source: str) -> Optional[Tuple[List[Source], List[Contributor]]]:
    """Loads a JSON file and attempts to parse it as either a datapackage or custom metadata."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            print(f"Warning: Expected dictionary in {file_path}, got {type(data)}")
            return None

        if "sources" in data:
            return _parse_as_datapackage(data, original_source)
            
        return _parse_as_custom_metadata(data, original_source)
    except Exception as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
        return None

def _extract_from_fallback_logic(original_source: str, search_path: Path) -> Tuple[List[Source], List[Contributor]]:
    """Final fallback that attempts to extract metadata from file system attributes/standard metadata.json."""
    title, desc, contact_email, created, published = extract_metadata(search_path)
    
    # If it's a handle, path should be blank. If local, it should be the original source.
    is_handle = is_handle_id(original_source)
    source_path = "" if is_handle else original_source
    source_handle = original_source if is_handle else ""

    source = Source(
        title=title,
        description=desc,
        path=source_path,
        handle=source_handle,
        created_date=created,
        published_date=published
    )
    
    contributors = []
    if contact_email:
        contributors.append(Contributor(
            title=contact_email.split("@")[0],
            email=contact_email,
            role=DEFAULT_CONTRIBUTOR_ROLE,
            datasets=[title]
        ))

    return [source], contributors

def extract_source_info(search_path: Path, original_source: str, metadata_filename: Optional[str] = None) -> Tuple[List[Source], List[Contributor]]:
    """
    Extracts source and contributor information from a dataset path.
    Prioritizes the specified `metadata_filename`, then 'datapackage.json', then 'metadata.json'.
    """
    # 1. Try specified metadata file (hidden metadata file in output dir)
    if metadata_filename:
        path = search_path / metadata_filename
        if path.exists():
            result = _load_and_parse_metadata(path, original_source)
            if result:
                return result

    # 2. Try standard fallbacks (datapackage.json, etc.)
    for filename in METADATA_FALLBACKS:
        path = search_path / filename
        if path.exists():
            result = _load_and_parse_metadata(path, original_source)
            if result:
                return result

    # 3. Last resort fallback based on directory analysis
    return _extract_from_fallback_logic(original_source, search_path)

def _update_contributors_map(contributors_map: Dict[str, Contributor], new_contributors: List[Contributor]):
    """Aggregates contributors into a central map to avoid duplicates."""
    for c in new_contributors:
        email = c.email
        if not email:
            continue
            
        if email not in contributors_map:
            contributors_map[email] = Contributor(
                title=c.title,
                email=email,
                role=c.role,
                datasets=[]
            )
            
        existing = contributors_map[email]
        for ds in c.datasets:
            if ds not in existing.datasets:
                existing.datasets.append(ds)

def finalize_domain_package(
    domain_path: Path,
    domain_name: str,
    spatial_source: str,
    dhw_source: str,
    connectivity_source: str,
    icc_source: str,
    cyclones_source: Optional[str] = None,
    waves_source: Optional[str] = None
):
    """
    Constructs the final Domain datapackage.json by aggregating metadata.
    """
    domain_dir_name = domain_path.name
    
    # Define resource configurations: (source, rel_path, res_name, format, extra, metadata_file)
    resources_config = [
        (spatial_source, f"spatial/{domain_dir_name}.gpkg", "spatial_data", "geopackage", {}, "spatial.metadata.json"),
        (dhw_source, "DHWs", "dhw", "netcdf", {}, "dhw.metadata.json"),
        (connectivity_source, "connectivity", "connectivity", "csv", {}, "connectivity.metadata.json"),
        (icc_source, "spatial/coral_cover.nc", "coral_cover", "netcdf", {}, "icc.metadata.json"),
    ]

    if cyclones_source:
        resources_config.append((cyclones_source, "cyclones", "cyclones", "netcdf", {}, "cyclones.metadata.json"))
    if waves_source:
        resources_config.append((waves_source, "waves", "waves", "netcdf", {}, "waves.metadata.json"))

    all_sources: List[Source] = []
    contributors_map: Dict[str, Contributor] = {}
    domain_resources: List[Resource] = []

    for src_input, rel_path, res_name, res_fmt, extra, meta_name in resources_config:
        target_path = domain_path / rel_path
        search_path = target_path if target_path.is_dir() else target_path.parent

        extracted_sources, extracted_contributors = extract_source_info(
            search_path, 
            original_source=src_input, 
            metadata_filename=meta_name
        )

        # Aggregate unique sources
        for s in extracted_sources:
            if not any(existing.title == s.title for existing in all_sources):
                all_sources.append(s)

        # Aggregate unique contributors
        _update_contributors_map(contributors_map, extracted_contributors)

        res = Resource(
            name=res_name,
            description=f"{res_name} data.",
            path=rel_path,
            format=res_fmt,
            **extra
        )
        domain_resources.append(res)

    # Finalize contributors list
    final_contributors = list(contributors_map.values())
    for c in final_contributors:
        c.update_description()

    domain_dp = DataPackage(
        name=domain_name,
        title=f"{domain_name} Domain",
        description=DEFAULT_DESCRIPTION,
        version=DATAPACKAGE_VERSION,
        sources=all_sources,
        contributors=final_contributors,
        resources=domain_resources,
        simulation_metadata=SimulationMetadata(timeframe=DEFAULT_TIMEFRAME)
    )

    output_file = domain_path / "datapackage.json"
    with open(output_file, "w") as f:
        f.write(domain_dp.model_dump_json(indent=4, exclude_none=True))

    print(f"Domain datapackage written to {output_file}")
