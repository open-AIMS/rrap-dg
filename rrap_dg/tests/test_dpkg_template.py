import pytest
import os
from rrap_dg.dpkg_template.dpkg_template import generate, package
from unittest.mock import patch
from rrap_dg.main import app


def test_generate_structure(cli_runner, tmp_path):
    """Test the generate command to ensure it creates the required directory structure
    and files.

    """
    result = cli_runner.invoke(app, ["template", "generate", str(tmp_path)])

    assert (
        result.exit_code == 0
    ), f"Expected exit code 0, got {
        result.exit_code}. Output: {result.output}"

    # Verify the directory structure and files
    for folder in ["connectivity", "cyclones", "dhws", "spatial", "waves"]:
        assert os.path.isdir(
            tmp_path / folder
        ), f"Expected {folder} directory to be created."
    assert os.path.isfile(tmp_path / "README.md"), "README.md file was not created."
    assert os.path.isfile(
        tmp_path / "datapackage.json"
    ), "datapackage.json file was not created."


# CLI test for the package command


@patch("rrap_dg.dpkg_template.utils.download_data")
def test_package_with_spec(mock_download_data, cli_runner, tmp_path, get_test_file):
    """est the package command with a spec file to ensure datasets download as specified."""
    # Run the CLI command using the spec_file fixture
    spec_file = get_test_file
    result = cli_runner.invoke(
        app, ["template", "package", str(tmp_path), str(spec_file)]
    )

    assert (
        result.exit_code == 0
    ), f"Expected exit code 0, got {
        result.exit_code}. Output: {result.output}"
    assert (
        mock_download_data.called
    ), "Expected download_data to be called for datasets."
