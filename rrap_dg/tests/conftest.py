import pytest
import json
import os
import toml
from typer.testing import CliRunner
from pathlib import Path


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="session")
def get_handle_id():
    """Load and return the handle_id from the test Toml file"""
    tom_file = os.path.join(os.path.dirname(__file__), "test_data.toml")

    with open(tom_file, "r") as file:
        data = toml.load(file)
        return data["datasets"][0]["id"]


@pytest.fixture
def get_test_file(tmp_path):
    """Fixture to the test_data.toml"""
    # Path to your test_data.json file
    test_data_path = Path(__file__).parent / "test_data.toml"
    return test_data_path
