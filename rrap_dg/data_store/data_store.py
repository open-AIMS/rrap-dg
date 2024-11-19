import typer
from rrap_dg.utils import download_data

app = typer.Typer()

# Define CLI command using download_data


@app.command(help="Download data from RRAP M&DS Data Store by handle id.")
def download(
    handle_id: str = typer.Argument(...), dest: str = typer.Argument(...)
) -> None:
    """Download data using the handle ID.

    Downloads the data to the specified destination directory.

    Args:
        handle_id (str): ID of the dataset to download.
        dest (str): destination directory to save the downloaded data.

    Raises:
        FileNotFoundError: destination directory not found.
        PermissionError: no permission to write to the destination directory.
        Exception: any unexpected errors not capture above during the download process.
    """

    try:
        print(f"Received handle_id: {handle_id}, dest: {dest}")
        download_data(handle_id, dest)
        print(f"Successfully downloaded data with handle ID '{handle_id}' to '{dest}'.")

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Error: The destination directory '{dest}' was not found. Reason: {e}"
        )

    except PermissionError as e:
        raise PermissionError(
            f"Error: Permission denied to write to the directory '{dest}'. Reason: {e}"
        )

    except Exception as e:
        raise Exception(
            f"An unexpected error occurred while accessing the directory '{dest}': {e}"
        )
