import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rrap_dg.datapackage import DataPackage, Resource, Source, Contributor, SimulationMetadata
from rrap_dg.utils import extract_metadata

def extract_source_info(source_path: Path, metadata_filename: Optional[str] = None) -> Tuple[List[Source], List[Contributor]]:
    """
    Extracts source and contributor information from a dataset path.
    Prioritizes the specified `metadata_filename`, then 'datapackage.json', then 'metadata.json'.
    """
    # Try specified metadata file
    if metadata_filename:
        specific_path = source_path / metadata_filename
        if specific_path.exists():
            # Try parsing as datapackage first
            try:
                with open(specific_path, "r") as f:
                    data = json.load(f)

                if "sources" in data:
                    # It's a datapackage
                    sources = [Source(**s) for s in data.get("sources", [])]
                    contributors = [Contributor(**c) for c in data.get("contributors", [])]
                    return sources, contributors
                else:
                    info = data.get("dataset_info", {})
                    associations = data.get("associations", {})
                    title = info.get("name", data.get("name", "Unknown Dataset"))
                    desc = info.get("description", data.get("description", ""))
                    contact = associations.get("point_of_contact")
                    created = info.get("created_date", {}).get("value")
                    published = info.get("published_date", {}).get("value")

                    source = Source(title=title, description=desc, path=str(source_path), created_date=created, published_date=published)
                    contributors = []
                    if contact:
                        contributors.append(Contributor(title=contact.split("@")[0], email=contact, role="author", datasets=[title]))
                    return [source], contributors

            except Exception as e:
                print(f"Warning: Failed to parse {specific_path}: {e}")

    # Fallback to standard datapackage.json
    dpkg_path = source_path / "datapackage.json"
    if dpkg_path.exists():
        try:
            with open(dpkg_path, "r") as f:
                data = json.load(f)
            sources = [Source(**s) for s in data.get("sources", [])]
            contributors = [Contributor(**c) for c in data.get("contributors", [])]
            return sources, contributors
        except Exception as e:
            print(f"Warning: Failed to parse datapackage.json at {source_path}: {e}")

    # Fallback to standard metadata.json
    title, desc, contact_email, created, published = extract_metadata(source_path)
    source = Source(
        title=title,
        description=desc,
        path=str(source_path),
        created_date=created,
        published_date=published
    )
    contributors = []
    if contact_email:
        contributors.append(Contributor(
            title=contact_email.split("@")[0],
            email=contact_email,
            role="author",
            datasets=[title]
        ))

    return [source], contributors

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

    # Map resource keys to their destination paths in the domain structure
    # Expected: (source_input_path, relative_domain_path, resource_name, format, extra_fields, metadata_filename)
    resources_config = [
        (spatial_source, "spatial/GBR_2026-01-20_v080.gpkg", "spatial_data", "geopackage", {}, "spatial_metadata.json"),
        (dhw_source, "DHWs", "dhw", "netcdf", {}, "dhw_datapackage.json"),
        (connectivity_source, "connectivity", "connectivity", "csv", {}, "connectivity_datapackage.json"),
        (icc_source, "spatial/coral_cover.nc", "coral_cover", "netcdf", {}, "icc_datapackage.json"),
    ]

    if cyclones_source:
        resources_config.append((cyclones_source, "cyclones", "cyclones", "netcdf", {}, "cyclones_datapackage.json"))
    if waves_source:
        resources_config.append((waves_source, "waves", "waves", "netcdf", {}, "waves_datapackage.json"))

    all_sources: List[Source] = []
    contributors_map: Dict[str, Contributor] = {}
    domain_resources: List[Resource] = []

    for src_input, rel_path, res_name, res_fmt, extra, meta_name in resources_config:
        target_path = domain_path / rel_path
        search_path = target_path if target_path.is_dir() else target_path.parent

        extracted_sources, extracted_contributors = extract_source_info(search_path, metadata_filename=meta_name)

        for s in extracted_sources:
            if not any(existing.title == s.title for existing in all_sources):
                all_sources.append(s)

        for c in extracted_contributors:
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

        res = Resource(
            name=res_name,
            description=f"{res_name} data.",
            path=rel_path,
            format=res_fmt,
            **extra
        )
        domain_resources.append(res)

    final_contributors = []
    for c in contributors_map.values():
        c.update_description()
        final_contributors.append(c)

    domain_dp = DataPackage(
        name=domain_name,
        title=f"{domain_name} Domain",
        description="Generated ADRIA Domain",
        version="0.8.0",
        sources=all_sources,
        contributors=final_contributors,
        resources=domain_resources,
        simulation_metadata=SimulationMetadata(timeframe=[2025, 2099])
    )

    output_file = domain_path / "datapackage.json"
    with open(output_file, "w") as f:
        f.write(domain_dp.model_dump_json(indent=4, exclude_none=True))

    print(f"Domain datapackage written to {output_file}")
