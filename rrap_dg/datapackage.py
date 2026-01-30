from typing import List, Optional
from pydantic import BaseModel, Field

class Contributor(BaseModel):
    title: str
    email: Optional[str] = None
    role: str = "author"
    datasets: List[str] = Field(default_factory=list)
    description: Optional[str] = None

    def update_description(self):
        if self.datasets:
            ds_str = ", ".join(self.datasets)
            self.description = f"Point of contact for: {ds_str}"
        else:
            self.description = "Contributor"

class Source(BaseModel):
    title: str
    description: Optional[str] = ""
    path: Optional[str] = None
    handle: str = ""
    created_date: Optional[str] = None
    published_date: Optional[str] = None

class Resource(BaseModel):
    name: str
    path: str
    description: str = ""
    format: str = "unknown"
    location_id_col: Optional[str] = None
    cluster_id_col: Optional[str] = None
    k_col: Optional[str] = None
    area_col: Optional[str] = None

class SimulationMetadata(BaseModel):
    timeframe: List[int]

class DataPackage(BaseModel):
    name: str
    title: str
    version: str
    description: str = "Generated ADRIA Domain"
    sources: List[Source]
    contributors: List[Contributor] = []
    simulation_metadata: Optional[SimulationMetadata] = None
    resources: List[Resource]
