from typing import Optional, Dict
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.validators import Validators
from app.utils.exceptions import ValidationError, AuthenticationError, ConflictError
from app.security.jwt_handler import JWTHandler

class AuthServiceFastAPI:
    """FastAPI authentication service"""

    def __init__(self):
        self.user_repo = UserRepository()
        self.validators = Validators()
        self.jwt_handler = JWTHandler()

    async def register(self, username: str, email: str, password: str) -> Dict:
        """Register new user"""
        # Validation
        if not self.validators.validate_username(username):
            raise ValidationError(
                "Некорректное имя пользователя (3-50 символов, буквы, цифры, _)")

        if not self.validators.validate_email(email):
            raise ValidationError("Некорректный email адрес")

        if not self.validators.validate_password(password):
            raise ValidationError("Пароль должен содержать минимум 6 символов")

        # Check uniqueness
        if self.user_repo.find_by_username(username):
            raise ConflictError("Пользователь с таким именем уже существует")

        if self.user_repo.find_by_email(email):
            raise ConflictError("Пользователь с таким email уже существует")

        # Create user
        user = User(
            username=username,
            email=email.lower(),
            password_hash=self.jwt_handler.get_password_hash(password),
            is_active=True,
            role='user'
        )

        user_id = self.user_repo.create(user)
        user.id = user_id

        # Generate tokens with STRING user_id (fixes JWT issue)
        token_data = {"sub": str(user_id), "username": username, "role": user.role}
        access_token = self.jwt_handler.create_access_token(token_data)
        refresh_token = self.jwt_handler.create_refresh_token({"sub": str(user_id)})

        return {
            'user_id': str(user_id),  # Return as string
            'username': username,
            'role': user.role,  # Add role for consistency
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    async def login(self, username: str, password: str) -> Dict:
        """User login"""
        user = self.user_repo.find_by_username(username)

        if not user:
            raise AuthenticationError("Неверное имя пользователя или пароль")

        if not self.jwt_handler.verify_password(password, user.password_hash):
            raise AuthenticationError("Неверное имя пользователя или пароль")

        if not user.is_active:
            raise AuthenticationError("Аккаунт деактивирован")

        # Generate tokens with STRING user_id (fixes JWT issue)
        token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
        access_token = self.jwt_handler.create_access_token(token_data)
        refresh_token = self.jwt_handler.create_refresh_token({"sub": str(user.id)})

        return {
            'user_id': str(user.id),  # Return as string
            'username': user.username,
            'role': user.role,  # Add role for admin check
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    async def refresh_token(self, user_id: str) -> str:
        """Refresh access token"""
        # Convert string user_id to int for database lookup
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise AuthenticationError("Неверный ID пользователя")

        user = self.user_repo.find_by_id(user_id_int)

        if not user or not user.is_active:
            raise AuthenticationError(
                "Пользователь не найден или деактивирован")

        # Generate new access token with STRING user_id
        token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
        return self.jwt_handler.create_access_token(token_data)

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.user_repo.find_by_id(user_id)