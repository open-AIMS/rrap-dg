import os
import json
import shutil
from os.path import join as pj
from datetime import datetime
from rrap_dg.utils import download_data

# Define the main folder structure and file rename mappings
STRUCTURE = ["connectivity", "cyclones", "dhws", "spatial", "waves"]
RENAME_MAP = {
    "readme": "README.md",
    "datapackage": "datapackage.json"
}

README_BASE = """
# ADRIA data package

Created: {created}

## Connectivity
## Cyclones
## DHWs
## Spatial
## Waves
"""


def create_directory_structure(base_path: str) -> None:
    """
    Create the specified directory structure in the base path.

    Parameters
    ----------
    base_path : str
        Path where the directory structure will be created.
    """
    try:
        for folder in STRUCTURE:
            os.makedirs(pj(base_path, folder), exist_ok=True)
        with open(pj(base_path, "datapackage.json"), "a") as dp_file:
            dp_file.write("{}")  # Initialize with empty JSON
        with open(pj(base_path, "README.md"), "a") as readme_file:
            readme_file.write(README_BASE.format(created=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    except Exception as e:
        print(f"Error creating directory structure at {base_path}: {e}")

def load_specification(spec_path: str) -> dict:
    """
    Load and return the JSON specification from a file.

    Parameters
    ----------
    spec_path : str
        Path to the JSON specification file.

    Returns
    -------
    dict
        Parsed JSON data from the file.
    """
    try:
        with open(spec_path, 'r') as spec_file:
            return json.load(spec_file)
    except FileNotFoundError:
        print(f"Specification file {spec_path} not found.")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in spec file {spec_path}: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error loading spec file {spec_path}: {e}")
        raise

def download_datasets(spec_data: dict, download_path: str) -> None:
    """
    Download datasets based on the specification data to the download path.

    Parameters
    ----------
    spec_data : dict
        Dictionary with dataset specifications.
    download_path : str
        Path where datasets will be downloaded.
    """
    for dataset in spec_data.get("datasets", []):
        dataset_id = dataset.get("id")
        output_dir = dataset.get("output_dir", "default")  # Use "default" if output_dir is not provided

        # Create the specific output directory within download_path
        specific_download_path = pj(download_path, output_dir)
        os.makedirs(specific_download_path, exist_ok=True)

        if dataset_id:
            print(f"Downloading dataset {dataset_id} to {specific_download_path}...")
            try:
                download_data(dataset_id, specific_download_path)
                print(f"Downloaded {dataset_id} to {specific_download_path}")
            except Exception as e:
                print(f"Failed to download dataset {dataset_id}: {e}")


def move_files_to_target(template_path: str, download_path: str) -> None:
    """
    Move files from the download path to their respective target folders in template_path 
    based on STRUCTURE and RENAME_MAP, while maintaining separation by `output_dir`.

    Parameters
    ----------
    template_path : str
        Path where the final structured data will be organized.
    download_path : str
        Temporary path where datasets are downloaded initially.
    """
    try:
        # Loop through each output directory within the download_path
        for output_dir in os.listdir(download_path):
            specific_download_path = pj(download_path, output_dir)

            # Process files and subfolders within each output_dir separately
            for root, dirs, files in os.walk(specific_download_path):
                
                # Move specific files based on RENAME_MAP (only if unique to each output_dir)
                for filename in files:
                    for prefix, target_name in RENAME_MAP.items():
                        if filename.lower().startswith(prefix):
                            source_path = pj(root, filename)
                            target_path = pj(template_path, output_dir, target_name)
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            try:
                                shutil.move(source_path, target_path)
                                print(f"Moved and renamed {filename} to {target_path}")
                            except Exception as e:
                                print(f"Error moving file {filename} to {target_path}: {e}")

                # Move files from specific subfolders to their corresponding target folders
                for subfolder_name in dirs:
                    # Determine the target folder based on folder structure
                    if "site" in subfolder_name.lower():
                        target_folder = pj(template_path, output_dir, "spatial")
                    elif subfolder_name.lower() in STRUCTURE:
                        target_folder = pj(template_path, output_dir, subfolder_name)
                    else:
                        continue

                    source_folder = pj(root, subfolder_name)
                    os.makedirs(target_folder, exist_ok=True)

                    # Move all files from source_folder to the specific target folder
                    for dirpath, _, filenames in os.walk(source_folder):
                        for filename in filenames:
                            file_path = pj(dirpath, filename)
                            try:
                                shutil.copy2(file_path, target_folder)
                            except Exception as e:
                                print(f"Error copying file {filename} to {target_folder}: {e}")
                    print(f"Flattened and moved all files from {source_folder} to {target_folder}")
    except Exception as e:
        print(f"Error moving files to target structure: {e}")
