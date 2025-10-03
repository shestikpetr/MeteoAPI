from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# Request schemas
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

# Response schemas
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours

class AuthLoginResponse(BaseModel):
    success: bool = True
    data: dict = Field(..., description="Contains user_id, username, access_token, refresh_token")

class RefreshTokenResponse(BaseModel):
    success: bool = True
    access_token: str

class UserMeResponse(BaseModel):
    success: bool = True
    data: UserResponse