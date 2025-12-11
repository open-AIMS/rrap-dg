import os
import shutil
import tempfile
import datetime
import json
from string import Template
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from typing import Dict, Optional, Any

from rrap_dg import DATAPACKAGE_VERSION, PKG_PATH # Import DATAPACKAGE_VERSION and PKG_PATH
from rrap_dg.dpkg_template.dpkg_template import generate as generate_dpkg # Import dpkg_template generator
from .config_model import DomainConfig
from .source_manager import SourceManager
from .formatters import FormatterRegistry
from .exceptions import ConfigurationError

class DomainBuilder:
    def __init__(self, config_path: str, output_parent_dir: str):
        self.config_path = config_path
        self.config = self._load_config()
        # Use a temporary directory for downloads that persists for the builder's life
        self._temp_dir = tempfile.mkdtemp(prefix="rrap_dg_builder_")
        # Pass all source configurations directly to the SourceManager
        self.source_manager = SourceManager(self._temp_dir, self.config.sources)
        
        # Construct the final output directory path based on naming convention
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        version_str = DATAPACKAGE_VERSION.replace(".", "")
        self._final_output_dir = os.path.join(
            output_parent_dir, # Use the argument here
            f"{self.config.domain_name}_{date_str}_v{version_str}"
        )

    def _load_config(self) -> DomainConfig:
        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)
        return DomainConfig(**data)

    def build(self):
        print(f"Building domain: {self.config.domain_name}")
        
        # Create final output directory and initial structure using dpkg_template
        # This creates basic folders and empty datapackage.json/README.md
        generate_dpkg(self._final_output_dir) 

        # Process each output
        for output_name, output in self.config.outputs.items():
            print(f"Processing output: {output_name} -> {output.filename} ({output.type})")
            
            # Resolve primary source using the updated SourceManager method
            source_path = self.source_manager.resolve_source_path(output.source)
            
            # Get formatter
            formatter = FormatterRegistry.get(output.formatter)
            
            # Construct output path using the final output directory
            output_path = os.path.join(self._final_output_dir, output.filename)
            output_parent = os.path.dirname(output_path)
            if output_parent:
                os.makedirs(output_parent, exist_ok=True) # Ensure specific output sub-directories exist
            
            # Execute format
            # Formatters can now call source_manager.resolve_source_path(key) for any auxiliary sources
            formatter.format(
                source_path=source_path,
                output_path=output_path,
                options=output.options,
                source_manager=self.source_manager
            )
            
        # After all outputs are processed, generate domain-level metadata (overwriting initial templates)
        self._generate_datapackage_json()
        self._generate_domain_readme()

        print("Build complete.")

    def _generate_datapackage_json(self):
        dpkg_path = os.path.join(self._final_output_dir, "datapackage.json")
        domain_name = self.config.domain_name
        
        # Extract metadata from source handles and global options
        sources_list = []
        contributors_dict = {}

        for source_key, source_config in self.config.sources.items():
            handle = source_config.handle
            resolved_path = self.source_manager.resolved_paths.get(source_key)
            meta_path = self.source_manager.get_source_metadata_path(source_key)
            
            if meta_path and os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    try:
                        meta = json.load(f)
                        dataset_info = meta.get("dataset_info", {})
                        associations = meta.get("associations", {})
                        
                        sources_list.append({
                            "title": dataset_info.get("name", f"{source_key} Dataset"),
                            "description": dataset_info.get("description", ""),
                            "path": resolved_path, # Or a relative path
                            "handle": handle or ""
                        })

                        contact = associations.get("point_of_contact")
                        if contact and contact not in contributors_dict:
                            contributors_dict[contact] = {
                                "title": contact.split("@")[0],
                                "email": contact,
                                "role": "author",
                                "description": f"Point of contact for {source_key} dataset"
                            }
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode metadata file for source '{source_key}' at {meta_path}")
            elif handle:
                 # Even if no metadata.json, add basic info if it was a handle
                 sources_list.append({
                    "title": f"{source_key} Dataset (Handle: {handle})",
                    "description": "",
                    "path": resolved_path,
                    "handle": handle
                 })
            elif resolved_path:
                 # Local path, just record path
                 sources_list.append({
                    "title": f"{source_key} Dataset (Local)",
                    "description": "",
                    "path": resolved_path,
                    "handle": ""
                 })

        # Dynamically determine num_locations if spatial geopackage is generated
        num_locations_val = None # Initialize as None, will be replaced with int if found
        spatial_output = next((out for out in self.config.outputs.values() if out.type == "spatial_data"), None)
        if spatial_output:
            gpkg_path = os.path.join(self._final_output_dir, spatial_output.filename)
            if os.path.exists(gpkg_path):
                try:
                    import geopandas as gpd # Import geopandas here to avoid module-level issues
                    gdf = gpd.read_file(gpkg_path)
                    num_locations_val = len(gdf) # Store as int directly
                except Exception as e:
                    print(f"Warning: Could not read geopackage at {gpkg_path} to determine num_locations. Error: {e}")
        
        # Extract global options for template substitution
        global_opts = self.config.global_options
        
        # Populate resources based on actual outputs
        resources_list = []
        for output_name, output_config in self.config.outputs.items():
            resource = {
                "name": output_name,
                "description": output_config.options.get("description", f"{output_name} data."),
                "path": output_config.filename,
                "format": output_config.options.get("format", "unknown"), # Allow format to be specified in output options
            }
            # Add specific columns for spatial data
            if output_config.type == "spatial_data": # Check type here
                resource["location_id_col"] = global_opts.get("location_id_col", "UNIQUE_ID")
                resource["cluster_id_col"] = global_opts.get("cluster_id_col", "UNIQUE_ID")
                resource["k_col"] = global_opts.get("k_col", "ReefMod_habitable_proportion")
                resource["area_col"] = global_opts.get("area_col", "ReefMod_area_m2")
            
            resources_list.append(resource)

        # Construct the datapackage dictionary directly
        datapackage_dict = {
            "name": domain_name,
            "title": f"{domain_name} Domain",
            "description": "Generated ADRIA Domain",
            "version": DATAPACKAGE_VERSION,
            "sources": sources_list,
            "simulation_metadata": {
                "timeframe": list(map(int, global_opts.get("timeframe", "2025 2099").split(" "))),
                "num_locations": num_locations_val
            },
            "contributors": list(contributors_dict.values()),
            "resources": resources_list
        }

        with open(dpkg_path, "w") as f:
            json.dump(datapackage_dict, f, indent=4)
        print(f"Generated {dpkg_path}")

    def _generate_domain_readme(self):
        readme_path = os.path.join(self._final_output_dir, "README.md")
        template_path = os.path.join(PKG_PATH, "format_gbr", "domain_readme.md.template")
        
        with open(template_path, "r") as f:
            template_content = f.read()
        
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        
        # Prepare substitution dictionary for the README template
        substitutions = {
            "domain_name": self.config.domain_name,
            "date_str": date_str,
            "version": DATAPACKAGE_VERSION.replace(".", ""),
            "location_id_col": self.config.global_options.get("location_id_col", "UNIQUE_ID"),
            "area_col": self.config.global_options.get("area_col", "ReefMod_area_m2"),
            "k_col": self.config.global_options.get("k_col", "ReefMod_habitable_proportion"),
            "cluster_id_col": self.config.global_options.get("cluster_id_col", "UNIQUE_ID")
        }
        
        # Add descriptions for generated outputs based on their 'description' in options
        # Ensure default values are provided if output.options.get('description') is None
        for output_name, output_config in self.config.outputs.items():
            if output_config.type == "dhw":
                substitutions["dhw_desc"] = output_config.options.get("description", "Degree heating week data.")
            elif output_config.type == "waves":
                substitutions["waves_desc"] = output_config.options.get("description", "Wave data.")
            elif output_config.type == "cyclones":
                substitutions["cyclones_desc"] = output_config.options.get("description", "Cyclone mortality data.")
        
        # Fill in missing descriptions if types not found in outputs
        substitutions.setdefault("dhw_desc", "No DHW data provided/available.")
        substitutions.setdefault("waves_desc", "No wave data provided/available.")
        substitutions.setdefault("cyclones_desc", "No cyclone data provided/available.")


        template = Template(template_content)
        content = template.substitute(**substitutions)
        
        with open(readme_path, "w") as f:
            f.write(content)
        print(f"Generated {readme_path}")

    def cleanup(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)