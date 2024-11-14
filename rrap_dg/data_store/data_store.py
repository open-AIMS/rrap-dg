import typer
from rrap_dg.utils import download_data

app = typer.Typer()

# Define CLI command using download_data


@app.command(help="Download data from RRAP M&DS Data Store by handle id.")
def download(
    handle_id: str = typer.Argument(...), dest: str = typer.Argument(...)
) -> None:
    """Download data using the handle ID.

    This function downloads the data to the specified destination directory.

        Parameters
        ----------
        handle_id : str
            The ID of the dataset to download.
        dest : str
            The destination directory to save the downloaded data.
    """

    try:
        print(f"Received handle_id: {handle_id}, dest: {dest}")
        download_data(handle_id, dest)
        print(f"Successfully downloaded data with handle ID '{handle_id}' to '{dest}'.")

    except FileNotFoundError:
        print(f"Error: The destination directory '{dest}' was not found.")
    except PermissionError:
        print(f"Error: Permission denied to write to '{dest}'. Check your permissions.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
