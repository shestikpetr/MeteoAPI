from dataclasses import dataclass
from typing import Optional


@dataclass
class Parameter:
    """Модель параметра"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    unit: str = ""
    description: Optional[str] = None
    category: Optional[str] = None


@dataclass
class SensorData:
    """Модель данных датчика"""
    time: int
    value: float
    parameter: str
    station: str
