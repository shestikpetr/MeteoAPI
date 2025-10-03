from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List


# Request schemas (deprecated - use parameter.py)
class SensorDataRequest(BaseModel):
    station: str = Field(..., description="Station number")
    parameter: str = Field(..., description="Parameter code")
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")


# Response schemas for sensor data
class TimeSeriesDataPoint(BaseModel):
    """Одна точка временного ряда"""
    time: int = Field(..., description="Unix timestamp")
    value: float = Field(..., description="Значение параметра")


class ParameterMetadata(BaseModel):
    """Метаданные параметра"""
    code: str = Field(..., description="Код параметра")
    name: str = Field(..., description="Название параметра")
    unit: Optional[str] = Field(None, description="Единица измерения")
    category: Optional[str] = Field(None, description="Категория")


class ParameterWithValue(BaseModel):
    """Параметр с текущим значением"""
    code: str = Field(..., description="Код параметра")
    name: str = Field(..., description="Название параметра")
    value: Optional[float] = Field(None, description="Текущее значение")
    unit: Optional[str] = Field(None, description="Единица измерения")
    category: Optional[str] = Field(None, description="Категория")


class StationDataResponse(BaseModel):
    """Данные одной станции (для мобилки)"""
    station_number: str = Field(..., description="Номер станции")
    custom_name: Optional[str] = Field(None, description="Пользовательское название")
    is_favorite: bool = Field(False, description="Избранная станция")
    location: Optional[str] = Field(None, description="Местоположение")
    latitude: Optional[float] = Field(None, description="Широта")
    longitude: Optional[float] = Field(None, description="Долгота")
    parameters: List[ParameterWithValue] = Field([], description="Параметры с значениями")
    timestamp: Optional[str] = Field(None, description="Время получения данных")


class AllStationsDataResponse(BaseModel):
    """Последние данные всех станций пользователя"""
    success: bool = True
    data: List[StationDataResponse]


class ParameterHistoryResponse(BaseModel):
    """Исторические данные параметра"""
    success: bool = True
    station_number: str = Field(..., description="Номер станции")
    parameter: ParameterMetadata = Field(..., description="Информация о параметре")
    data: List[TimeSeriesDataPoint] = Field(..., description="Временной ряд")
    count: int = Field(..., description="Количество записей")