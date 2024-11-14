import tempfile
from unittest.mock import patch
from rrap_dg.main import app


@patch("rrap_dg.data_store.data_store.download_data")
def test_download_command(mock_download_data, cli_runner, get_handle_id):
    handle_id = get_handle_id
    with tempfile.TemporaryDirectory() as dest:
        result = cli_runner.invoke(app, ["data-store", "download", handle_id, dest])

        # Verify exit code and check output
        assert (
            result.exit_code == 0
        ), f"Expected command to exit with code 0, got {
            result.exit_code}. Output: {result.output}"

        # Assert download_data was called with the correct arguments
        mock_download_data.assert_called_once_with(handle_id, dest)
        assert mock_download_data.called, "Expected download_data to be called."
