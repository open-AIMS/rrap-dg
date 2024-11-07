# global utils.py
from rrap_dg.config import get_provena_client
from asyncio import run

def download_data(handle_id: str, dest: str) -> None:
    """
    Download data from the RRAP M&DS data store using a handle id.

    Parameters
    ----------
    handle_id : str
        Dataset ID of the connectivity matrices.
    dest : str
        Output location for downloaded connectivity matrices.

    Raises
    ------
    ValueError
        If an invalid handle ID or destination is provided.
    ConnectionError
        If there is an issue connecting to the Provena data store.
    Exception
        For other unexpected errors.
    """
    try:
        provena = get_provena_client()
        print(f"Attempting to download dataset with ID: {handle_id} to destination: {dest}")
        
        # Run download in an asynchronous context
        run(
            provena.datastore.io.download_all_files(
                destination_directory=dest, dataset_id=handle_id
            )
        )
        
        print(f"Download successful for dataset {handle_id} to {dest}")

    except ValueError as ve:
        print(f"ValueError: {ve}. Check if the handle_id or destination path is correct.")
        raise  

    except ConnectionError:
        print("ConnectionError: Unable to connect to the Provena data store. Please check your connection.")
        raise

    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        raise
