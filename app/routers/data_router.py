from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.schemas.sensor import (
    AllStationsDataResponse,
    StationDataResponse,
    ParameterHistoryResponse
)
from app.services.sensor_data_service import SensorDataService
from app.security.dependencies import get_current_user
from app.utils.exceptions import MeteoAPIException
from app.models.user import User

router = APIRouter()
data_service = SensorDataService()


@router.get("/latest", response_model=AllStationsDataResponse)
async def get_all_stations_latest_data(current_user: User = Depends(get_current_user)):
    """Получить последние данные всех станций пользователя

    Главный эндпоинт для мобилки: один запрос возвращает все станции
    с их местоположением и последними значениями ТОЛЬКО видимых параметров.

    Ответ включает:
    - Номер станции и пользовательское название
    - Местоположение (location, latitude, longitude)
    - Параметры с текущими значениями (только видимые)
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        stations_data = data_service.get_all_stations_latest_data(user_id)

        return AllStationsDataResponse(data=stations_data)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{station_number}/latest", response_model=StationDataResponse)
async def get_station_latest_data(
    station_number: str,
    current_user: User = Depends(get_current_user)
):
    """Получить последние данные одной станции

    Возвращает последние значения ТОЛЬКО видимых параметров станции
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        station_data = data_service.get_station_latest_data(
            user_id=user_id,
            station_number=station_number
        )

        return station_data

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{station_number}/{parameter_code}/history",
            response_model=ParameterHistoryResponse)
async def get_parameter_history(
    station_number: str,
    parameter_code: str,
    start_time: Optional[int] = Query(None, description="Unix timestamp начала периода"),
    end_time: Optional[int] = Query(None, description="Unix timestamp конца периода"),
    limit: int = Query(1000, ge=1, le=10000, description="Максимум записей"),
    current_user: User = Depends(get_current_user)
):
    """Получить исторические данные параметра за период

    Пользователь заходит на станцию и выбирает параметр для просмотра истории.
    Возвращает временной ряд значений параметра.

    Параметры:
    - station_number: номер станции (8 цифр)
    - parameter_code: код параметра (например, 4402)
    - start_time: начало периода (Unix timestamp), опционально
    - end_time: конец периода (Unix timestamp), опционально
    - limit: максимальное количество записей (по умолчанию 1000, максимум 10000)

    Примечания:
    - Параметр должен быть видимым для пользователя
    - Данные возвращаются в порядке убывания времени (свежие первыми)
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        history = data_service.get_parameter_history(
            user_id=user_id,
            station_number=station_number,
            parameter_code=parameter_code,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        return ParameterHistoryResponse(**history)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))