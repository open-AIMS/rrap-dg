import tempfile
from unittest.mock import patch
from rrap_dg.main import app
from unittest.mock import patch, MagicMock

@patch("rrap_dg.utils.download_data")
def test_download_command(mock_download_data, cli_runner, get_handle_id):
    """Test to download a file using handle ID"""
    handle_id = get_handle_id

    with tempfile.TemporaryDirectory() as dest:
        # Run the CLI command
        result = cli_runner.invoke(
            app, ["data-store", "download", str(handle_id),str(dest)]
        )

        # Verify exit code and check output
        assert (
                result.exit_code == 0
        ), f"Expected command to exit with code 0, got {result.exit_code}. Output: {result.output}"
