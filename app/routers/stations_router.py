from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from app.schemas.station import (
    UserStationRequest, UserStationListResponse
)
from app.services.station_management_service import StationManagementService
from app.security.dependencies import get_current_user
from app.utils.exceptions import MeteoAPIException
from app.models.user import User

router = APIRouter()
station_service = StationManagementService()


@router.get("", response_model=UserStationListResponse)
async def get_user_stations(current_user: User = Depends(get_current_user)):
    """Получить все станции пользователя

    Возвращает список станций без параметров и данных
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id
        stations = station_service.get_user_stations(user_id)

        return UserStationListResponse(data=stations)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_user_station(
    station_data: UserStationRequest,
    current_user: User = Depends(get_current_user)
):
    """Добавить станцию пользователю

    Пользователь вводит номер станции (8 цифр) и может дать ей свое название.
    При добавлении все параметры станции становятся видимыми по умолчанию.
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        result = station_service.add_user_station(
            user_id=user_id,
            station_number=station_data.station_id,
            custom_name=station_data.custom_name
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Станция с указанным номером не существует"
            )

        return {
            'success': True,
            'data': result
        }

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{station_number}")
async def update_user_station(
    station_number: str,
    custom_name: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Обновить настройки станции пользователя

    Можно изменить пользовательское название и/или пометить как избранную
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        success = station_service.update_user_station(
            user_id=user_id,
            station_number=station_number,
            custom_name=custom_name,
            is_favorite=is_favorite
        )

        return {'success': success}

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{station_number}")
async def remove_user_station(
    station_number: str,
    current_user: User = Depends(get_current_user)
):
    """Удалить станцию у пользователя

    При удалении также удаляются все настройки видимости параметров
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        success = station_service.remove_user_station(
            user_id=user_id,
            station_number=station_number
        )

        return {'success': success}

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))