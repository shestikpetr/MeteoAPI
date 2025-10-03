from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.user import (
    UserRegisterRequest, UserLoginRequest,
    AuthLoginResponse, RefreshTokenResponse, UserMeResponse, UserResponse
)
from app.services.auth_service_fastapi import AuthServiceFastAPI
from app.security.dependencies import get_current_user, verify_refresh_token
from app.utils.exceptions import MeteoAPIException
from app.models.user import User

router = APIRouter()
auth_service = AuthServiceFastAPI()

@router.post("/register", response_model=AuthLoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterRequest):
    """Регистрация нового пользователя"""
    try:
        result = await auth_service.register(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )

        return AuthLoginResponse(data=result)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login", response_model=AuthLoginResponse)
async def login(credentials: UserLoginRequest):
    """Вход пользователя"""
    try:
        result = await auth_service.login(
            username=credentials.username,
            password=credentials.password
        )

        return AuthLoginResponse(data=result)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(user_id: str = Depends(verify_refresh_token)):
    """Обновление access токена"""
    try:
        access_token = await auth_service.refresh_token(user_id)
        return RefreshTokenResponse(access_token=access_token)

    except MeteoAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    user_response = UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

    return UserMeResponse(data=user_response)


@router.post("/logout")
async def logout():
    """Выход пользователя (клиентский logout)"""
    return {"message": "Успешный выход. Удалите токены на клиенте."}