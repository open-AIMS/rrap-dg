import typer
from rrap_dg.dpkg_template.utils import *

app = typer.Typer()


@app.command(help="Create empty ADRIA Domain data package")
def generate(template_path: str) -> None:
    """Generate the ADRIA Domain data package structure.

    Creates an empty data package structure at the given template path.

    Args:
        template_path (str): The path where the data package structure will be created.

    Raises:
        FileNotFoundError:  template path does not exist.
        PermissionError: insufficient permissions to create the structure.
        ValueError: path format is invalid.
        Exception: any other unexpected errors.
    """
    try:
        create_directory_structure(template_path)
        print(f"Generated package structure in {template_path}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The path '{template_path}' does not exist.")
    except PermissionError:
        raise PermissionError(f"Error: Insufficient permissions at '{template_path}'.")
    except ValueError:
        raise ValueError(f"Error: Invalid path format for '{template_path}'.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


@app.command(help="Create empty ADRIA Domain data package")
def package(template_path: str, spec: str) -> None:
    """Create an ADRIA Domain data package pre-filled with data from a data store.

    Generates a directory structure based on a specified template
    path and populates it with datasets defined in a TOML specification file.


    Args:
        template_path (str): Path where the data package structure will be created.
        spec (str): Path to the TOML file

    Raises:
        FileNotFoundError: Specified template path or TOML file path does not exist.
        PermissionError: Permission issues accessing directories or files.
        toml.TomlDecodeError: TOML file format is invalid or contains parsing errors.
        Exception: Any other unexpected errors that occur during loading/downloading/moving datasets.
    """
    # Generate directory structure if it doesn't exist
    if not os.path.exists(template_path):
        try:
            generate(template_path)
        except PermissionError:
            raise PermissionError(
                f"Error: Insufficient permissions to create structure at '{template_path}'."
            )
        except Exception as e:
            raise Exception(
                f"OS error while creating structure at '{template_path}': {e}"
            )

    # Load the TOML file
    try:
        spec_data = toml.load(spec)
        structure_ids = get_structure_ids(spec_data)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"The specification file '{spec}' could not be found. Reason: {e}"
        )
    except toml.TomlDecodeError as e:
        raise toml.TomlDecodeError(
            f"The TOML file '{spec}' has invalid formatting. Reason : {e}"
        )
    except Exception as e:
        raise Exception(
            f"An unexpected error occurred while loading the specification file '{spec}'. Reason: {e}"
        )

    # Iterate over each dataset in the TOML file, download it, and move to the respective structure
    for dataset_id, dataset_dir in structure_ids.items():
        # Validate the dataset ID
        if not dataset_id or len(dataset_id.strip()) == 0:
            print(
                f"Error: 'id' must be present and non-empty. Found empty id for {dataset_dir}."
            )
            continue

        # Create a temporary download directory within template_path
        temp_download_dir = os.path.join(template_path, "temp_download")
        os.makedirs(temp_download_dir, exist_ok=True)

        # Download the dataset based on its ID to the temporary folder
        try:
            download_data(dataset_id, temp_download_dir)
        except Exception as e:
            raise Exception(f"Error downloading dataset with ID '{dataset_id}': {e}")

        # Move files from temp_download_dir to the target directory
        target_dir_path = os.path.join(template_path, dataset_dir)
        os.makedirs(target_dir_path, exist_ok=True)

        try:
            move_files_to_target(target_dir_path, temp_download_dir)
        except PermissionError as e:
            raise PermissionError(
                f"Error: Insufficient permissions to move data to '{target_dir_path}'. Reason:{e}"
            )
        except Exception as e:
            raise Exception(
                f"OS error while moving files to '{target_dir_path}'. Reason:{e}"
            )

        # Cleanup the temporary download directory
        shutil.rmtree(temp_download_dir)

    print("Package creation complete.")


@app.command(
    help="Generate an ADRIA Domain package using an older MD store package, pre-filled with relevant downloaded data"
)
def upgrade(template_path: str, spec: str) -> None:
    """Upgrade an ADRIA Domain data package.

    Upgrades an older package from the data store with data by formatting into the new  package structure.


    Args:
        template_path (str): Final package path
        spec (str): TOML file path

    Raises:
        FileNotFoundError: TOML file or specified paths do not exist.
        PermissionError: Insufficient permission to create directories or write files.
        ValueError: Fields in the dataset (e.g., `output_dir` or `id`) are missing.
        toml.TomlDecodeError: Invalid TOML file format.
        Exception: Any other unexpected errors during the upgrade process.
    """
    print("Starting package creation...")

    # Load specification data from the TOML file
    try:
        spec_data = toml.load(spec)
        datasets = spec_data.get("datasets", [])
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Error: The specification file '{spec}' could not be found. Reason:{e}"
        )

    except toml.TomlDecodeError as e:
        raise toml.TomlDecodeError(
            f"Error: The TOML file '{spec}' contains invalid formatting. Reason:{e}"
        )

    except Exception as e:
        raise Exception(f"Error loading spec file '{spec}'. Reason: {e}")

    # Iterate over each dataset in the TOML file and create directory structures
    for dataset in datasets:
        dataset_id = dataset.get("id")
        if not dataset_id:  # Skip the dataset if `id` is not present or empty
            print("Warning: Skipping dataset with missing 'id' field.")
            continue

        output_dir = dataset.get("output_dir")

        # Ensure both `output_dir` and `id` are present
        if not output_dir or not dataset_id:
            print(
                f"Error: Both 'output_dir' and 'id' are required. Found 'output_dir': {output_dir}, 'id': {dataset_id}"
            )

        target_dir = os.path.join(template_path, output_dir)
        print(f"Creating structure for: {target_dir}")

        # Generate directory structure doesn't exist
        if not os.path.exists(target_dir):
            generate(target_dir)

        # Create temporary download directory within target_dir
        temp_download_dir = os.path.join(target_dir, "temp_download")
        try:
            os.makedirs(temp_download_dir, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Error: Insufficient permissions to create '{temp_download_dir}'. Reason:{e}"
            )
        except Exception as e:
            raise Exception(
                f"Unexpected error creating temporary download directory '{temp_download_dir}': {e}"
            )

        # Download datasets based on specification
        download_datasets(dataset, temp_download_dir)

        # Move downloaded files to target folders within target_dir
        move_files_to_target(target_dir, temp_download_dir)

        # Clean up temporary download directory after processing
        try:
            shutil.rmtree(temp_download_dir)
            print(f"Temporary download folder for '{output_dir}' cleaned up.")
        except PermissionError as e:
            raise PermissionError(
                f"Error: Insufficient permissions to delete '{temp_download_dir}'. Reason:{e}"
            )
        except Exception as e:
            raise Exception(
                f"Error cleaning up temporary download folder '{temp_download_dir}': {e}"
            )

    print("Package upgrade complete.")
