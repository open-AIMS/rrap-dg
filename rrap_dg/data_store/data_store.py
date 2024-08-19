import typer
from rrap_dg.config import get_provena_client
from asyncio import run

app = typer.Typer()


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
