from rrap_dg.config import get_provena_client
import typer
from asyncio import run

app = typer.Typer()


@app.command(help="Download connectivity matrices from M&DS datastore")
def download(dest: str, dataset_id: str) -> None:
    """Download connectivity matrices for a given cluster using the dataset id.

    Parameters
    ----------
    dest: str, output location of downloaded connectivity matrices
    dataset_id: str, dataset id of the connectivity matrices
    """
    provena = get_provena_client()
    run(
        provena.datastore.io.download_all_files(
            destination_directory=dest, dataset_id=dataset_id
        )
    )
