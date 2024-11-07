
import pytest
import tempfile
from rrap_dg.utils import download_data
from unittest.mock import patch, AsyncMock, MagicMock


@patch("rrap_dg.utils.get_provena_client")
def test_download_data_function(mock_get_client,get_handle_id):
    """
    Test the download_data function to ensure it calls Provena's download_all_files.
    """
    from rrap_dg.utils import download_data
    
    mock_client = MagicMock()
    mock_datastore = MagicMock()
    mock_io = AsyncMock()
    
    mock_client.datastore = mock_datastore
    mock_datastore.io = mock_io
    mock_get_client.return_value = mock_client

    handle_id=get_handle_id
    with tempfile.TemporaryDirectory() as dest:
        download_data(handle_id, dest)
        mock_io.download_all_files.assert_called_once_with(
            destination_directory=dest, dataset_id=handle_id
        )