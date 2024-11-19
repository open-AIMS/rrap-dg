import os
import json
import pytest
import tempfile
import toml
from unittest.mock import patch, MagicMock, call
from rrap_dg.dpkg_template.utils import (
    create_directory_structure,
    load_specification,
    download_datasets,
    move_files_to_target,
)


def test_create_directory_structure_creates_folders(tmp_path):
    """Test to  create directory structure successfully"""
    create_directory_structure(tmp_path)

    # Check for expected folder structure
    for folder in ["connectivity", "cyclones", "dhws", "spatial", "waves"]:
        assert os.path.isdir(tmp_path / folder), f"{folder} directory was not created."

    # Check for required files
    assert os.path.isfile(tmp_path / "README.md"), "README.md was not created."
    assert os.path.isfile(
        tmp_path / "datapackage.json"
    ), "datapackage.json was not created."


def test_load_specification_valid_file(tmp_path, get_test_file):
    """Test to load specification loads content correctly from a valid TOML file."""

    # Create a valid spec JSON file
    spec_content = {"datasets": [{"id": "67890"}]}
    spec_file = tmp_path / "spec.toml"
    spec_file.write_text(toml.dumps(spec_content))

    # Load and assert content
    spec_data = load_specification(spec_file)
    assert spec_data == spec_content


def test_load_specification_file_not_found():
    """Test to load specification and raises FileNotFoundError when the file is missing."""
    with pytest.raises(FileNotFoundError):
        load_specification("non_existent_spec.toml")


@patch("rrap_dg.dpkg_template.utils.download_data")
def test_download_datasets_successful_download(mock_download_data, get_test_file):
    """Test to download datasets and ensure datasets are downloaded successfully when IDs are present"""
    dataset = {"id": "12345"}
    download_path = "/tmp/test_download"

    download_datasets(dataset, download_path)

    # Assert download_data was called with the correct parameters
    mock_download_data.assert_called_once_with("12345", download_path)

@patch("rrap_dg.dpkg_template.utils.download_data")
def test_download_datasets_missing_id(mock_download_data):
    """Test to ensures no download attempts are made when 'id' is missing in dataset entries."""
    spec_data = {"datasets": [{}]}  # Missing "id" in dataset

    with tempfile.TemporaryDirectory() as dest:
        download_datasets(spec_data, dest)

    # Assert: Verify that download_data was not called due to missing id
    mock_download_data.assert_not_called()
