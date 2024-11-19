import os
import shutil
import toml
from datetime import datetime
from rrap_dg.utils import download_data
from fuzzywuzzy import process

# Define the main folder structure and file rename mappings
STRUCTURE = ["connectivity", "cyclones", "dhws", "spatial", "waves"]
RENAME_MAP = {"readme": "README.md", "datapackage": "datapackage.json"}

README_BASE = """
# ADRIA data package

Created: {created}

## Connectivity
## Cyclones
## DHWs
## Spatial
## Waves
"""


def get_structure_ids(spec_data):
    """Map structure IDs from the specification data.

    Uses fuzzy matching to align TOML structure keys with predefined structure
    names in `STRUCTURE`.

    Args:
        spec_data (dict): TOML file.

    Returns:
        dict: Dictionary of mapping dataset IDs to structure names.
    """
    structure_ids = {}
    toml_structure_keys = list(spec_data.keys())
    try:
        for structure in STRUCTURE:
            # get the match
            best_match, similarity = process.extractOne(structure, toml_structure_keys)

            # Only consider matches that are more than 70% similar to the original string, in case of misspellings in the TOML file

            if similarity > 70 and "id" in spec_data[best_match]:
                # replace with the corrected structure key name
                spec_data[structure] = spec_data.pop(best_match)
                structure_ids[spec_data[structure]["id"]] = structure
    except TypeError as e:
        raise TypeError(
            f"Error: Invalid type or unexpected format in TOML file {spec_data}. Reason:{e}"
        )
    except Exception as e:
        raise Exception(f"Unexpected error. Reason: {e}")

    return structure_ids


def create_directory_structure(base_path: str) -> None:
    """Create the specified directory structure in the base path.


    Args:
        base_path (str): Path to the directory structure .

    Raises:
        FileNotFoundError: Path does not exist and cannot be created.
        PermissionError: Insufficient permissions to write to path
        Exception: Any other unexpected errors.
    """
    try:
        # Create each folder in the structure
        for folder in STRUCTURE:
            os.makedirs(os.path.join(base_path, folder), exist_ok=True)

        # Initialize an empty datapackage.json file
        try:
            with open(os.path.join(base_path, "datapackage.json"), "w") as dp_file:
                dp_file.write("{}")  # Initialize with empty JSON
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Error: Could not find 'datapackage.json'. Reason:{e}"
            )
        except PermissionError as e:
            raise PermissionError(f"Error: Insufficient permissions. Reason:{e}")
        except Exception as e:
            raise Exception(f"Unexpected error writing to {base_path}. Reason:{e}")

        # Create a README.md file with a timestamp
        try:
            with open(os.path.join(base_path, "README.md"), "w") as readme_file:
                readme_file.write(
                    README_BASE.format(
                        created=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Error: 'README.md' not found in {base_path}. Reason:{e}"
            )
        except PermissionError as e:
            raise PermissionError(
                f"Error: Insufficient permissions to write 'README.md'. Reason:{e}"
            )
        except Exception as e:
            raise Exception(f"Unexpected error writing 'README.md'. Reason:{e}")

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Cannot create directory '{base_path}': No such file or directory. Reason: {e}"
        )
    except PermissionError as e:
        raise PermissionError(
            f"Cannot create directory '{base_path}': Insufficient permissions. Reason: {e}"
        )
    except Exception as e:
        raise Exception(
            f"An unexpected error occurred while creating the directory '{base_path}': {e}"
        )


def load_specification(spec_path: str) -> dict:
    """Load and return the TOML specification from a file.

    Args:
        spec_path (str): Path to the TOML specification file.

    Returns:
        dict: Parsed TOML data.

    Raises:
        FileNotFoundError: TOML file not found.
        toml.TomlDecodeError: Error parsing the TOML file.
        PermissionError: Insufficient permissions to write to path
        Exception: Any other unexpected errors during loading.
    """
    try:
        with open(spec_path, "r") as spec_file:
            return toml.load(spec_file)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Error: Specification file '{spec_path}' not found. Reason:{e}"
        )
    except toml.TomlDecodeError as e:
        raise toml.TomlDecodeError(
            f"Failed to decode TOML in '{spec_path}'. Reason:{e}"
        )
    except PermissionError as e:
        raise PermissionError(f"Error: Insufficient permissions. Reason:{e}")
    except Exception as e:
        raise Exception(
            f"An unexpected error occurred while loading the specification file. Reason:{e}"
        )


def download_datasets(dataset: dict, download_path: str) -> None:
    """Download a dataset based on the specification data to the download path.

    Args:
        dataset (dict): Dictionary containing dataset's specifications.
        download_path (str): Output path to download the dadaset.

    Raises:
        FileNotFoundError: Dataset not found in the data store.
        PermissionError: Insufficient permissions to write to the download path.
        Exception: Any unexpected errors while downloading.
    """
    dataset_id = dataset.get("id")

    try:
        os.makedirs(download_path, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"Error: Insufficient permissions to create directory '{download_path}'. Reason: {e}"
        )
    except Exception as e:
        raise Exception(
            f"An unexpected error occurred while creating directory structure. Reason: {e}"
        )

    if dataset_id:
        print(f"Downloading dataset {dataset_id} to {download_path}...")
        try:
            download_data(dataset_id, download_path)
            print(f"Downloaded {dataset_id} to {download_path}")
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Error: Dataset '{dataset_id}' not found. Reason:{e}"
            )
        except PermissionError as e:
            raise PermissionError(
                f"Error: Insufficient permissions to write to '{download_path}'. Reason:{e}"
            )
        except Exception as e:
            raise Exception(f"Failed to download dataset {dataset_id}. Reason:{e}")


def move_files_to_target(template_path: str, download_path: str) -> None:
    """Move files from download_path to structured folders in template_path.

    Args:
        template_path (str): Path to the final structured data.
        download_path (str): Temporary to save the downloaded dataset.

    Raises:
        FileNotFoundError: Source file or directory is missing.
        PermissionError: IInsufficient permissions to access/modify files.
        Exception: Any unexpected errors while moving files.
    """
    try:
        # Loop through each output directory within the download_path
        for output_dir in os.listdir(download_path):
            specific_download_path = os.path.join(download_path, output_dir)

            # Check if this is a file and move
            if os.path.isfile(specific_download_path):
                try:
                    shutil.move(specific_download_path, template_path)
                    print(
                        f"Moved and overwritten file {os.path.basename(specific_download_path)} to {template_path}"
                    )
                except PermissionError as e:
                    raise PermissionError(
                        f"Permission denied moving file {specific_download_path} to {template_path}. Reason: {e}"
                    )
                except FileNotFoundError as e:
                    raise FileNotFoundError(
                        f"File not found: {specific_download_path}. Reason: {e}"
                    )
                except Exception as e:
                    raise Exception(
                        f"Error moving file {os.path.basename(specific_download_path)} to {template_path}: {e}"
                    )

            # Process files and subfolders within each output_dir separately
            for root, dirs, files in os.walk(specific_download_path):
                # Move specific files based on RENAME_MAP (only if unique to each output_dir)
                for filename in files:
                    for prefix, _ in RENAME_MAP.items():
                        if filename.lower().startswith(prefix):
                            source_path = os.path.join(root, filename)
                            target_path_file = os.path.join(template_path, filename)
                            try:
                                if os.path.exists(target_path_file):
                                    os.remove(target_path_file)
                                    print(
                                        f"Overwritten existing file at {target_path_file}"
                                    )
                                shutil.move(source_path, target_path_file)
                                print(
                                    f"Moved and renamed {filename} to {template_path}"
                                )
                            except FileNotFoundError as e:
                                raise FileNotFoundError(
                                    f"File not found: {source_path}. Reason: {e}"
                                )
                            except PermissionError as e:
                                raise PermissionError(
                                    f"Permission denied for moving {filename} to {template_path}. Reason:{e}"
                                )
                            except Exception as e:
                                raise Exception(
                                    f"Error moving file {filename} to {template_path}: {e}"
                                )

                # Move files from specific subfolders to their corresponding target folders
                for subfolder_name in dirs:
                    # Determine the target folder based on folder structure
                    if "site" in subfolder_name.lower():
                        target_folder = os.path.join(template_path, "spatial")
                    elif subfolder_name.lower() in STRUCTURE:
                        target_folder = os.path.join(template_path, subfolder_name)
                    else:
                        continue

                    source_folder = os.path.join(root, subfolder_name)
                    os.makedirs(target_folder, exist_ok=True)

                    # Move all files from source_folder to the specific target folder
                    for dirpath, _, filenames in os.walk(source_folder):
                        for filename in filenames:
                            file_path = os.path.join(dirpath, filename)
                            try:
                                shutil.copy2(file_path, target_folder)
                            except FileNotFoundError as e:
                                raise FileNotFoundError(
                                    f"File not found: {file_path}. Reason:{e}"
                                )
                            except PermissionError as e:
                                raise PermissionError(
                                    f"Permission denied when copying {file_path} to {target_folder}. Reason:{e}"
                                )
                            except Exception as e:
                                raise Exception(
                                    f"Error copying file {filename} to {target_folder}: {e}"
                                )
                    print(
                        f"Flattened and moved all files from {source_folder} to {target_folder}"
                    )

    except Exception as e:
        raise Exception(f"Error moving files to target structure: {e}")
