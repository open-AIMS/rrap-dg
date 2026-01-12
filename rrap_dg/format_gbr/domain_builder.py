import os
import datetime
import json
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from rrap_dg import DATAPACKAGE_VERSION
from rrap_dg.config import get_settings
from rrap_dg.dpkg_template.dpkg_template import generate as generate_dpkg

from .source_manager import SourceManager
from .formatters import FormatterRegistry
from .exceptions import ConfigurationError
from .models import DomainConfig, DataPackage, Source, Contributor, Resource, SimulationMetadata

def _process_contributor_metadata(contact, title, contributors):
    """Construct contributor models and check for multiple contributions."""
    if not contact:
        return

    if contact not in contributors:
        contributors[contact] = Contributor(
            title=contact.split("@")[0],
            email=contact,
            role="author",
            datasets=[]
        )
    contributors[contact].datasets.append(title)

    return


def _process_source_metadata(metadata_fn):
    """Extract metadata from source metadata file."""
    with open(metadata_fn, "r") as f:
        meta = json.load(f)
        dataset_info = meta.get("dataset_info", {})
        associations = meta.get("associations", {})

        title = dataset_info.get("name", metadata_fn)
        desc = dataset_info.get("description", "")

        contact = associations.get("point_of_contact")

    return title, desc, contact

def _process_resource_metadata(config_items, global_options):
    """Construct the resource models from the configuration."""
    resources = []
    for output_name, output_config in config_items:
        res_kwargs = {
            "name": output_name,
            "description": output_config.options.get("description", f"{output_name} data."),
            "path": output_config.filename,
            "format": output_config.options.get("format", "unknown")
        }

        if output_config.type == "spatial_data":
            res_kwargs.update({
                "location_id_col": global_options.get("location_id_col", "UNIQUE_ID"),
                "cluster_id_col": global_options.get("cluster_id_col", "UNIQUE_ID"),
                "k_col": global_options.get("k_col", "ReefMod_habitable_proportion"),
                "area_col": global_options.get("area_col", "ReefMod_area_m2")
            })

        resources.append(Resource(**res_kwargs))

    return resources

class DomainBuilder:
    def __init__(self, config_path: str, output_parent_dir: str):
        self.config_path = config_path
        self.config = self._load_config()

        settings = get_settings()
        self._cache_dir = settings.data_store_cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)

        self.source_manager = SourceManager(self._cache_dir, self.config.sources)

        date_str = datetime.date.today().strftime('%Y-%m-%d')
        version_str = DATAPACKAGE_VERSION.replace(".", "")
        self._final_output_dir = os.path.join(
            output_parent_dir,
            f"{self.config.domain_name}_{date_str}_v{version_str}"
        )

    @property
    def output_dir(self) -> str:
        return self._final_output_dir

    def _load_config(self) -> DomainConfig:
        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)
        return DomainConfig(**data)

    def build(self):
        print(f"Building domain: {self.config.domain_name}")

        generate_dpkg(self._final_output_dir)

        domain_dir_name = os.path.basename(self._final_output_dir)
        for output in self.config.outputs.values():
            if output.type == "spatial_data":
                new_filename = os.path.join("spatial", f"{domain_dir_name}.gpkg")
                print(f"Enforcing spatial filename: {new_filename}")
                output.filename = new_filename

        for output_name, output in self.config.outputs.items():
            print(f"Processing output: {output_name} -> {output.filename} ({output.type})")

            source_path = self.source_manager.resolve_source_path(output.source)

            formatter = FormatterRegistry.get(output.formatter)

            output_path = os.path.join(self._final_output_dir, output.filename)
            output_parent = os.path.dirname(output_path)
            if output_parent:
                os.makedirs(output_parent, exist_ok=True)

            try:
                formatter.format(
                    source_path=source_path,
                    output_path=output_path,
                    options=output.options,
                    source_manager=self.source_manager
                )
            except Exception as e:
                if "ValidationError" in str(type(e)):
                    raise ConfigurationError(f"Invalid options for formatter '{output.formatter}' in output '{output_name}': {e}")
                raise e

        self._generate_datapackage_json()

        print("Build complete.")

    def _generate_datapackage_json(self):
        dpkg_path = os.path.join(self._final_output_dir, "datapackage.json")
        domain_name = self.config.domain_name

        sources = []
        contributors = {}

        for source_key, source_config in self.config.sources.items():
            handle = source_config.handle
            resolved_path = self.source_manager.resolved_paths.get(source_key)
            meta_path = self.source_manager.get_source_metadata_path(source_key)

            title = f"{source_key} Dataset"
            desc = ""

            title, desc, contact = _process_source_metadata(meta_path)
            _process_contributor_metadata(contact, title, contributors)

            # Create Source object
            sources.append(Source(
                title=title,
                description=desc,
                path=resolved_path,
                handle=handle or ""
            ))

        global_opts = self.config.global_options
        resources = _process_resource_metadata(
            self.config.outputs.items(), global_opts
        )

        pkg = DataPackage(
            name=domain_name,
            title=f"{domain_name} Domain",
            version=DATAPACKAGE_VERSION,
            sources=sources,
            simulation_metadata=SimulationMetadata(
                timeframe=list(map(int, global_opts.get("timeframe", "2025 2099").split(" "))),
            ),
            contributors=contributors.values(),
            resources=resources
        )

        with open(dpkg_path, "w") as f:
            f.write(pkg.model_dump_json(exclude_none=True, indent=4))
        print(f"Generated {dpkg_path}")
