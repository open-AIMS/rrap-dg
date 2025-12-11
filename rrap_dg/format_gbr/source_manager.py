import os
from typing import Dict, Optional
from glob import glob
from rrap_dg.data_store.data_store import get_provena_client
from .config_model import SourceConfig
from .exceptions import SourceError, ConfigurationError

class SourceManager:
    """
    Manages the resolution and retrieval of data sources.
    Ensures that handles are downloaded only once.
    """
    def __init__(self, cache_dir: str, source_configs: Dict[str, SourceConfig]):
        self.cache_dir = cache_dir
        self.source_configs = source_configs
        self.resolved_paths: Dict[str, str] = {}
        self.metadata_paths: Dict[str, Optional[str]] = {} # New: Stores path to metadata.json for handles
        self._provena_client = None

    def get_provena_client(self):
        if self._provena_client is None:
             self._provena_client = get_provena_client()
        return self._provena_client

    def resolve_source_path_from_config(self, source_name: str, config: SourceConfig) -> str:
        """
        Returns the local directory path for a given source configuration object.
        If it's a handle, it downloads it to the temp directory (cached).
        If it's a path, it verifies existence.
        Populates self.metadata_paths for downloaded handles.
        """
        if source_name in self.resolved_paths:
            return self.resolved_paths[source_name]

        config.validate_source()

        if config.path:
            if not os.path.exists(config.path):
                raise SourceError(f"Source '{source_name}' path does not exist: {config.path}")
            self.resolved_paths[source_name] = config.path
            self.metadata_paths[source_name] = None # No metadata.json for local paths usually
            return config.path

        if config.handle:
            # Use sanitized handle as directory name to ensure uniqueness and caching across different configs
            sanitized_handle = config.handle.replace("/", "_")
            download_dest = os.path.join(self.cache_dir, sanitized_handle)
            
            # Check if already downloaded in this session or previously
            # (Simple check: if directory exists and is not empty)
            if os.path.exists(download_dest) and os.listdir(download_dest):
                print(f"Source '{source_name}' (Handle: {config.handle}) found in cache: {download_dest}")
                self.resolved_paths[source_name] = download_dest
                meta_path = os.path.join(download_dest, "metadata.json")
                self.metadata_paths[source_name] = meta_path if os.path.exists(meta_path) else None
                return download_dest
            
            print(f"Downloading source '{source_name}' (handle: {config.handle}) to {download_dest}...")
            try:
                import asyncio
                client = self.get_provena_client()
                asyncio.run(
                    client.datastore.io.download_all_files(
                        destination_directory=download_dest, 
                        dataset_id=config.handle
                    )
                )
                
                self.resolved_paths[source_name] = download_dest
                meta_path = os.path.join(download_dest, "metadata.json")
                self.metadata_paths[source_name] = meta_path if os.path.exists(meta_path) else None
                return download_dest
            except Exception as e:
                raise SourceError(f"Failed to download source '{source_name}': {str(e)}") from e

        raise SourceError(f"Invalid configuration for source '{source_name}'")

    def resolve_source_path(self, source_name: str) -> str:
        """
        Resolves a source by its name (key) from the internally held source_configs.
        """
        if source_name not in self.source_configs:
            raise ConfigurationError(f"Source key '{source_name}' not found in configuration sources.")
        
        return self.resolve_source_path_from_config(source_name, self.source_configs[source_name])

    def get_source_metadata_path(self, source_name: str) -> Optional[str]:
        """
        Returns the path to the metadata.json file for a resolved source handle, if available.
        Requires the source to have been resolved first.
        """
        if source_name not in self.resolved_paths:
            raise SourceError(f"Source '{source_name}' has not been resolved yet. Resolve it first.")
        return self.metadata_paths.get(source_name)
