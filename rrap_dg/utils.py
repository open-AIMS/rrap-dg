# global utils.py
from rrap_dg.config import get_provena_client
from asyncio import run


def download_data(handle_id: str, dest: str) -> None:
    """Download data from the RRAP M&DS data store using a handle id.

    Args:
        handle_id (str): Dataset ID
        dest (str): Output location.

    Raises:
        ValueError: Invalid handle ID or destination provided.
        ConnectionError: Connection issues.
        Exception: Any unexpected errors during the download process.
    """
    try:
        provena = get_provena_client()
        print(
            f"Attempting to download dataset with ID: {handle_id} to destination: {dest}"
        )

        # Run download in an asynchronous context
        run(
            provena.datastore.io.download_all_files(
                destination_directory=dest, dataset_id=handle_id
            )
        )

        print(f"Download successful for dataset {handle_id} to {dest}")
    except ValueError as ve:
        raise ValueError(
            f"Invalid handle ID or destination path. Ensure that handle_id '{handle_id}' and destination '{dest}' are correct. Reason: {ve}"
        )
    except ConnectionError as ce:
        raise ConnectionError(
            f"Unable to connect to the Provena data store. Reason: {ce}"
        )
    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred while downloading dataset '{handle_id}' to '{dest}'. Reason: {e}"
        )
