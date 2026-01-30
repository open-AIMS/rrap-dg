import json
import typer
from pathlib import Path
from typing import Tuple, Optional

def extract_metadata(dataset_path: Path) -> Tuple[str, str, Optional[str], Optional[str], Optional[str]]:
    """
    Tries to read metadata.json or ro-crate-metadata.json.
    Returns (title, description, point_of_contact, created_date, published_date)
    """
    search_path = dataset_path if dataset_path.is_dir() else dataset_path.parent
    
    meta_files = ["metadata.json", "ro-crate-metadata.json"]
    for mf in meta_files:
        p = search_path / mf
        if p.exists():
            try:
                with open(p, "r") as f:
                    data = json.load(f)
                
                # Handle Provena/RRAP metadata structure
                info = data.get("dataset_info", {})
                associations = data.get("associations", {})
                
                title = info.get("name", data.get("name", "Unknown Dataset"))
                desc = info.get("description", data.get("description", ""))
                contact = associations.get("point_of_contact")
                
                created = info.get("created_date", {}).get("value")
                published = info.get("published_date", {}).get("value")
                
                return title, desc, contact, created, published
            except Exception as e:
                print(f"Warning: Failed to parse {p}: {e}")
    
    return "Unknown Dataset", "No description available.", None, None, None

def validate_metadata_presence(path: Path) -> bool:
    """
    Checks if metadata.json exists in the given path.
    If path is a file, checks its parent.
    Warns the user and asks if they want to abort to supply it.
    """
    search_path = path if path.is_dir() else path.parent
    
    meta_files = ["metadata.json", "ro-crate-metadata.json"]
    found = any((search_path / mf).exists() for mf in meta_files)
    
    if not found:
        typer.secho(f"\nWARNING: No metadata.json found in {search_path}", fg=typer.colors.YELLOW, bold=True)
        typer.echo("Metadata is crucial for dataset provenance.")
        typer.echo(f"Please place a 'metadata.json' file in the root of: {search_path}\n")
        
        if not typer.confirm("Do you want to continue without metadata?", default=False):
            typer.echo("Aborted by user.")
            raise typer.Exit(code=1)

        return False
    
    return True