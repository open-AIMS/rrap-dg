from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

class Source(BaseModel):
    title: str
    description: Optional[str] = ""
    path: Optional[str] = None
    handle: Optional[str] = ""

class SimulationMetadata(BaseModel):
    timeframe: List[int]

class Contributor(BaseModel):
    title: str
    email: Optional[str] = None
    role: Optional[str] = "author"
    datasets: List[str] = Field(default_factory=list, exclude=True)

    @computed_field
    @property
    def description(self) -> str:
        if not self.datasets:
            return "Contributor"
        datasets_str = ", ".join(self.datasets)
        return f"Point of contact for: {datasets_str}"

class Resource(BaseModel):
    name: str
    description: str
    path: str
    format: str = "unknown"

    # Spatial specific fields
    location_id_col: Optional[str] = None
    cluster_id_col: Optional[str] = None
    k_col: Optional[str] = None
    area_col: Optional[str] = None

class DataPackage(BaseModel):
    name: str
    title: str
    description: str = "Generated ADRIA Domain"
    version: str
    sources: List[Source] = Field(default_factory=list)
    simulation_metadata: SimulationMetadata
    contributors: List[Contributor] = Field(default_factory=list)
    resources: List[Resource] = Field(default_factory=list)
