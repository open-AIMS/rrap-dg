import typer
from rrap_dg.dpkg_template.utils import *

app = typer.Typer()

@app.command(help="Create empty ADRIA Domain data package")
def generate(template_path: str) -> None:
    """
    Generate the ADRIA Domain data package structure at the specified template path.

    Parameters
    ----------
    template_path : str
        Path where the data package structure will be created.
    """
    try:
        create_directory_structure(template_path)
        print(f"Generated package structure in {template_path}")
    except Exception as e:
        print(f"Error generating package structure in {template_path}: {e}")

@app.command(help="Create ADRIA Domain data package pre-filling with data from data store")
def package(template_path: str, spec: str) -> None:
    """
    Create an ADRIA Domain data package, filling it with data from the data store based on a specification.

    Parameters
    ----------
    template_path : str
        Path where the final data package will be organized.
    spec : str
        Path to the JSON specification file listing datasets to download.
    """
    print("Starting package creation...")

    # Generate directory structure if it doesn't exist
    if not os.path.exists(template_path):
        generate(template_path)
    
    # Load specification data from the json
    try:
        spec_data = load_specification(spec)
    except Exception as e:
        print(f"Error loading spec file {spec}: {e}")
        return

    # Create temporary download directory within template_path
    temp_download_dir = pj(template_path, "temp_download")
    try:
        os.makedirs(temp_download_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating temporary download directory {temp_download_dir}: {e}")
        return

    # Download datasets based on specification
    try:
        download_datasets(spec_data, temp_download_dir)
    except Exception as e:
        print(f"Error downloading datasets: {e}")
        return
    
    # Move downloaded files to target folders within template_path
    try:
        move_files_to_target(template_path, temp_download_dir)
    except Exception as e:
        print(f"Error moving files to target folders: {e}")
        return

    # Clean up temporary download directory after processing
    try:
        shutil.rmtree(temp_download_dir)
        print("Temporary download folder cleaned up.")
    except Exception as e:
        print(f"Error cleaning up temporary download folder {temp_download_dir}: {e}")

    print("Package creation complete.")
