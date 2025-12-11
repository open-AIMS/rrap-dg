from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class SourceConfig(BaseModel):
    """Configuration for a single data source."""
    handle: Optional[str] = None
    path: Optional[str] = None
    type: Optional[str] = None  # metadata about source type (e.g. 'reefmod', 'netcdf')

    def validate_source(self):
        if not self.handle and not self.path:
            raise ValueError("Source must have either a 'handle' or a 'path'.")
        if self.handle and self.path:
            raise ValueError("Source cannot have both 'handle' and 'path'.")

class OutputConfig(BaseModel):
    """Configuration for a single output file."""
    type: str # e.g., 'connectivity', 'dhw', 'spatial'
    formatter: str # e.g., 'rme_connectivity', 'standard_netcdf'
    source: str # Key referencing a source in the sources map
    filename: str # Output filename (relative to output dir)
    
    # Additional formatter-specific arguments
    # e.g. spatial_source="canonical", rcps="2.6 4.5"
    options: Dict[str, Any] = Field(default_factory=dict)

class DomainConfig(BaseModel):
    """Root configuration for the domain generation."""
    domain_name: str
    
    # Global options available to all formatters if needed
    global_options: Dict[str, Any] = Field(default_factory=dict)
    
    sources: Dict[str, SourceConfig]
    outputs: Dict[str, OutputConfig]
