import typer
import os
import shutil
from rrap_dg.config import get_provena_client, get_settings
from asyncio import run

app = typer.Typer()


@app.command(help="Download data from RRAP M&DS Data Store by handle id and save to cache.")
def download_w_cache(handle_id: str, force: bool = False) -> str:
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

async def download_specific_file_async(handle_id: str, s3_path: str, dest: str) -> None:
    provena = get_provena_client()
    await provena.datastore.io.download_specific_file(
        dataset_id=handle_id,
        s3_path=s3_path,
        destination_directory=dest,
    )


async def list_all_files_async(handle_id: str) -> list[str]:
    provena = get_provena_client()
    files = await provena.datastore.io.list_all_files(dataset_id=handle_id)

    # The client returns S3Path objects. We need to return paths relative
    # to the dataset root for download_specific_file to work correctly.
    # The dataset root prefix is usually 'datasets/<sanitized_handle>/'.
    sanitized = handle_id.replace(".", "-").replace("/", "-")

    relative_files = []
    for f in files:
        # Get the full key (path within the bucket)
        key = f.key if hasattr(f, "key") else str(f)

        # Strip the prefix up to and including the sanitized handle
        if sanitized in key:
            _, _, rel = key.partition(sanitized + "/")
            if rel:
                relative_files.append(rel)
            else:
                # If it's the directory itself, we keep the original key or skip
                relative_files.append(key)
        else:
            relative_files.append(key)

    return relative_files


@app.command(help="Download specific file/folder from RRAP M&DS Data Store.")
def download_file(handle_id: str, s3_path: str, dest: str) -> None:
    """
    Download a specific file or folder from the RRAP M&DS data store.

    Args:
        handle_id: The dataset handle ID.
        s3_path: The S3 path of the file or folder to download.
        dest: The destination directory to save files to.
    """
    run(download_specific_file_async(handle_id, s3_path, dest))


@app.command(help="List all files in a dataset from RRAP M&DS Data Store.")
def list_files(handle_id: str) -> None:
    """
    List all files in a dataset from the RRAP M&DS data store.

    Args:
        handle_id: The dataset handle ID.
    """
    files = run(list_all_files_async(handle_id))
    for f in files:
        print(f)


@app.command(help="Download data from RRAP M&DS Data Store by handle id.")
def download(handle_id: str, dest: str) -> None:
    """
    Download data from the RRAP M&DS data store using a handle id.

    Args:
        dest: str, output location of downloaded connectivity matrices
        handle_id: str, dataset id of the connectivity matrices
    """
    provena = get_provena_client()
    run(
        provena.datastore.io.download_all_files(
            destination_directory=dest, dataset_id=handle_id
        )
    )
