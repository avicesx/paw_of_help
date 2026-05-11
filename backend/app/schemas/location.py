from pydantic import BaseModel
from typing import List, Literal, Optional

LocationType = Literal["organization", "volunteer", "foster_request"]

class LocationNearbyRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 5.0
    limit: int = 10
    types: List[LocationType] = ["organization", "volunteer", "foster_request"]