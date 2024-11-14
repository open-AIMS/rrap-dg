import os
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock, call
from rrap_dg.dpkg_template.utils import (
    create_directory_structure,
    load_specification,
    download_datasets,
    move_files_to_target,
)


def test_create_directory_structure_creates_folders(tmp_path):
    """
    Test that create_directory_structure successfully creates the required folders
    and files in the specified path.
    """
    create_directory_structure(tmp_path)

    # Check for expected folder structure
    for folder in ["connectivity", "cyclones", "dhws", "spatial", "waves"]:
        assert os.path.isdir(tmp_path / folder), f"{folder} directory was not created."

    # Check for required files
    assert os.path.isfile(tmp_path / "README.md"), "README.md was not created."
    assert os.path.isfile(
        tmp_path / "datapackage.json"
    ), "datapackage.json was not created."


def test_load_specification_valid_file(tmp_path):
    """
    Test load_specification loads content correctly from a valid JSON file.
    """
    # Create a valid spec JSON file
    spec_content = {"datasets": [{"id": "67890"}]}
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec_content))

    # Load and assert content
    spec_data = load_specification(spec_file)
    assert spec_data == spec_content


def test_load_specification_file_not_found():
    """
    Test load_specification raises FileNotFoundError when the file is missing.
    """
    with pytest.raises(FileNotFoundError):
        load_specification("non_existent_spec.json")


@patch("rrap_dg.dpkg_template.utils.download_data")
def test_download_datasets_successful_download(mock_download_data):
    """
    Test download_datasets to ensure datasets are downloaded successfully when IDs are present,
    with each dataset going to its specified output directory.
    """
    # Define test data with unique output directories for each dataset
    test_data = {
        "datasets": [
            {"id": "167890", "output_dir": "test"},
            {"id": "67890", "output_dir": "test2"},
        ]
    }

    # Create a temporary directory to act as the download base path
    with tempfile.TemporaryDirectory() as dest:
        download_datasets(test_data, dest)

        # Construct the expected paths, normalizing paths
        expected_call_1 = call("167890", os.path.normpath(os.path.join(dest, "test")))
        expected_call_2 = call("67890", os.path.normpath(os.path.join(dest, "test2")))

        # Assert that the download calls were made with the specific output directories
        mock_download_data.assert_has_calls(
            [expected_call_1, expected_call_2], any_order=True
        )
        assert mock_download_data.call_count == 2


@patch("rrap_dg.dpkg_template.utils.download_data")
def test_download_datasets_missing_id(mock_download_data):
    """Test download_datasets ensures no download attempts are made when 'id' is missing in dataset entries."""
    spec_data = {"datasets": [{}]}  # Missing "id" in dataset

    with tempfile.TemporaryDirectory() as dest:
        download_datasets(spec_data, dest)

    # Assert: Verify that download_data was not called due to missing id
    mock_download_data.assert_not_called()
