from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

# Request schemas
class StationCreateRequest(BaseModel):
    station_number: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = None

class StationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = None
    is_active: Optional[bool] = None

class UserStationRequest(BaseModel):
    station_id: str
    custom_name: Optional[str] = None
    is_favorite: bool = False

# Response schemas
class StationResponse(BaseModel):
    id: str
    station_number: str
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserStationResponse(BaseModel):
    id: str
    user_id: str
    station_id: str
    custom_name: Optional[str] = None
    is_favorite: bool = False
    created_at: Optional[datetime] = None
    station: Optional[StationResponse] = None

    model_config = ConfigDict(from_attributes=True)

class StationParameterResponse(BaseModel):
    id: str
    station_id: str
    parameter_code: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class StationListResponse(BaseModel):
    success: bool = True
    data: List[StationResponse]

class UserStationListResponse(BaseModel):
    success: bool = True
    data: List[UserStationResponse]