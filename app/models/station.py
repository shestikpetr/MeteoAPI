from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Station:
    """Модель станции"""
    id: Optional[int] = None
    station_number: str = ""
    name: str = ""
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UserStation:
    """Связь пользователя со станцией"""
    id: Optional[int] = None
    user_id: int = 0
    station_id: int = 0
    custom_name: Optional[str] = None
    is_favorite: bool = False
    created_at: Optional[datetime] = None


@dataclass
class StationParameter:
    """Параметры станции"""
    id: Optional[int] = None
    station_id: int = 0
    parameter_code: str = ""
    is_active: bool = True
