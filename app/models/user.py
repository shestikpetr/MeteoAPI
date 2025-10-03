from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    role: str = "user"  # user, admin
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
