from pydantic import BaseModel, Field
from typing import List, Optional


# Request schemas
class ParameterVisibilityUpdateRequest(BaseModel):
    """Запрос на изменение видимости одного параметра"""
    is_visible: bool = Field(..., description="Видимость параметра")


class BulkParameterVisibilityRequest(BaseModel):
    """Запрос на массовое изменение видимости параметров"""
    parameters: List[dict] = Field(
        ...,
        description="Список параметров с видимостью",
        example=[
            {"code": "4402", "visible": True},
            {"code": "5402", "visible": False}
        ]
    )


# Response schemas
class ParameterInfoResponse(BaseModel):
    """Информация о параметре"""
    code: str = Field(..., description="Код параметра")
    name: str = Field(..., description="Название параметра")
    unit: Optional[str] = Field(None, description="Единица измерения")
    description: Optional[str] = Field(None, description="Описание параметра")
    category: Optional[str] = Field(None, description="Категория параметра")


class ParameterWithVisibilityResponse(ParameterInfoResponse):
    """Параметр с информацией о видимости"""
    is_visible: bool = Field(..., description="Видимость для пользователя")
    display_order: int = Field(0, description="Порядок отображения")


class ParameterValueResponse(BaseModel):
    """Значение параметра"""
    code: str = Field(..., description="Код параметра")
    name: str = Field(..., description="Название параметра")
    value: Optional[float] = Field(None, description="Значение")
    unit: Optional[str] = Field(None, description="Единица измерения")
    category: Optional[str] = Field(None, description="Категория")


class ParameterListResponse(BaseModel):
    """Список параметров"""
    success: bool = True
    data: List[ParameterWithVisibilityResponse]


class BulkUpdateResponse(BaseModel):
    """Результат массового обновления"""
    success: bool = True
    updated: int = Field(..., description="Количество обновленных записей")
    total: int = Field(..., description="Общее количество записей")