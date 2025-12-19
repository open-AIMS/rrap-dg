import typer
import os
import shutil
from rrap_dg.config import get_provena_client, get_settings
from asyncio import run

app = typer.Typer()


@app.command(help="Download data from RRAP M&DS Data Store by handle id and save to cache.")
def fetch_dataset(handle_id: str, force: bool = False) -> str:
    """
    Retrieves a dataset, using the system cache if available.
    Returns the path to the dataset directory.
    
    Args:
        handle_id: The dataset handle ID.
        force: If True, delete any existing cached data and re-download.
    """
    settings = get_settings()
    cache_root = settings.data_store_cache_dir
    sanitized_handle = handle_id.replace("/", "_")
    target_dir = os.path.join(cache_root, sanitized_handle)

    if os.path.exists(target_dir):
        if force:
            print(f"Force enabled. Cleaning existing cache at {target_dir}...")
            shutil.rmtree(target_dir)
        elif os.listdir(target_dir):
            print(f"Dataset {handle_id} found in cache: {target_dir}")
            return target_dir

    print(f"Downloading dataset {handle_id} to cache: {target_dir}...")
    provena = get_provena_client()
    run(
        provena.datastore.io.download_all_files(
            destination_directory=target_dir, dataset_id=handle_id
        )
    )
    return target_dir


@app.command(help="Download data from RRAP M&DS Data Store by handle id.")
def download(handle_id: str, dest: str) -> None:
    """Download data from the RRAP M&DS data store using a handle id.

    Parameters
    ----------
    dest: str, output location of downloaded connectivity matrices
    handle_id: str, dataset id of the connectivity matrices
    """
    provena = get_provena_client()
    run(
        provena.datastore.io.download_all_files(
            destination_directory=dest, dataset_id=handle_id
        )
    )
