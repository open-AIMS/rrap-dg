from pathlib import Path
from typing import Dict, List, Any

from rrap_dg.datapackage import DataPackage, Resource, Source, Contributor
from rrap_dg.utils import extract_metadata

def finalize_dataset(
    output_path: str,
    sources: Dict[str, str],
    formatter_name: str,
    resource_name: str = "output_resource",
    resource_description: str = "Formatted data",
    resource_format: str = "unknown"
):
    """
    Generates the datapackage.json for a formatted dataset.
    """
    output_dir = Path(output_path)
    
    dp_sources = []
    contributors_map: Dict[str, Contributor] = {}

    for key, path_str in sources.items():
        path = Path(path_str)
        if not path.exists():
            continue
            
        title, desc, contact, created, published = extract_metadata(path)
        
        dp_sources.append(Source(
            title=title,
            description=f"{desc} (Role: {key})",
            path=str(path),
            handle=key,
            created_date=created,
            published_date=published
        ))

        if contact:
            if contact not in contributors_map:
                contributors_map[contact] = Contributor(title=contact.split("@")[0], email=contact)
            contributors_map[contact].datasets.append(title)

    final_contributors = []
    for c in contributors_map.values():
        c.update_description()
        final_contributors.append(c)

    resource = Resource(
        name=resource_name,
        description=resource_description,
        path=".",
        format=resource_format
    )

    dpkg = DataPackage(
        name=output_dir.name,
        title=f"Formatted {formatter_name} Dataset",
        version="0.1.0",
        sources=dp_sources,
        contributors=final_contributors,
        resources=[resource]
    )

    dpkg_path = output_dir / "datapackage.json"
    with open(dpkg_path, "w") as f:
        f.write(dpkg.model_dump_json(indent=4, exclude_none=True))
    
    print(f"Datapackage generated at: {dpkg_path}")