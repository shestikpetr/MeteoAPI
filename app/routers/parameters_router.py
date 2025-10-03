from fastapi import APIRouter, HTTPException, Depends
from app.schemas.parameter import (
    ParameterVisibilityUpdateRequest,
    BulkParameterVisibilityRequest,
    ParameterListResponse,
    BulkUpdateResponse
)
from app.services.parameter_visibility_service import ParameterVisibilityService
from app.security.dependencies import get_current_user
from app.utils.exceptions import MeteoAPIException
from app.models.user import User

router = APIRouter()
parameter_service = ParameterVisibilityService()


@router.get("/{station_number}/parameters", response_model=ParameterListResponse)
async def get_station_parameters(
    station_number: str,
    current_user: User = Depends(get_current_user)
):
    """Получить все параметры станции с информацией о видимости

    Возвращает список всех параметров станции с флагами видимости для пользователя
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        parameters = parameter_service.get_station_parameters(
            user_id=user_id,
            station_number=station_number
        )

        return ParameterListResponse(data=parameters)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{station_number}/parameters/{parameter_code}")
async def update_parameter_visibility(
    station_number: str,
    parameter_code: str,
    request: ParameterVisibilityUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Изменить видимость одного параметра

    Позволяет скрыть или показать параметр для пользователя
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        success = parameter_service.set_parameter_visibility(
            user_id=user_id,
            station_number=station_number,
            parameter_code=parameter_code,
            is_visible=request.is_visible
        )

        return {
            'success': success,
            'parameter_code': parameter_code,
            'is_visible': request.is_visible
        }

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{station_number}/parameters", response_model=BulkUpdateResponse)
async def bulk_update_parameters_visibility(
    station_number: str,
    request: BulkParameterVisibilityRequest,
    current_user: User = Depends(get_current_user)
):
    """Массовое изменение видимости параметров

    Позволяет одним запросом изменить видимость нескольких параметров

    Пример запроса:
    ```json
    {
        "parameters": [
            {"code": "4402", "visible": true},
            {"code": "5402", "visible": false},
            {"code": "700", "visible": true}
        ]
    }
    ```
    """
    try:
        user_id = str(current_user.id) if isinstance(current_user.id, int) else current_user.id

        result = parameter_service.bulk_set_visibility(
            user_id=user_id,
            station_number=station_number,
            parameters=request.parameters
        )

        return BulkUpdateResponse(
            success=True,
            updated=result['updated'],
            total=result['total']
        )

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))