from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

class SourceConfig(BaseModel):
    """Configuration for a single data source."""
    handle: Optional[str] = None
    path: Optional[str] = None
    type: Optional[str] = None

    def validate_source(self):
        if not self.handle and not self.path:
            raise ValueError("Source must have either a 'handle' or a 'path'.")
        if self.handle and self.path:
            raise ValueError("Source cannot have both 'handle' and 'path'.")

class OutputConfig(BaseModel):
    """Configuration for a single output file."""
    type: str
    formatter: str
    source: str
    filename: str

    options: Dict[str, Any] = Field(default_factory=dict)

class DomainConfig(BaseModel):
    """Root configuration for the domain generation."""
    domain_name: str

    global_options: Dict[str, Any] = Field(default_factory=dict)

    sources: Dict[str, SourceConfig]
    outputs: Dict[str, OutputConfig]

    @validator("sources")
    def validate_spatial_source_exists(cls, v: Dict[str, SourceConfig]):
        has_spatial = any(s == "spatial_base" for s in v.keys())
        if not has_spatial:
            raise ValueError("Configuration must contain at least one source with type='spatial_base'.")
        return v
