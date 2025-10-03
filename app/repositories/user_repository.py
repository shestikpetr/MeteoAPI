from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.user import User
from app.database.connection import DatabaseManager


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""

    def __init__(self):
        self.db = DatabaseManager.get_local_db()

    def find_by_id(self, id: int) -> Optional[User]:
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE id = %s",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def find_by_username(self, username: str) -> Optional[User]:
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def find_by_email(self, email: str) -> Optional[User]:
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def find_all(self) -> List[User]:
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]

    def create(self, user: User) -> int:
        with self.db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO users 
                (username, email, password_hash, is_active, role, created_at) 
                VALUES (%s, %s, %s, %s, %s, NOW())""",
                (user.username, user.email, user.password_hash,
                 user.is_active, user.role)
            )
            return cursor.lastrowid

    def update(self, user: User) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute(
                """UPDATE users 
                SET email = %s, is_active = %s, role = %s, updated_at = NOW()
                WHERE id = %s""",
                (user.email, user.is_active, user.role, user.id)
            )
            return cursor.rowcount > 0

    def delete(self, id: int) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (id,))
            return cursor.rowcount > 0

    def get_user_count(self) -> int:
        """Получить общее количество пользователей"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            return result['count'] if result else 0

    def get_active_user_count(self) -> int:
        """Получить количество активных пользователей"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            result = cursor.fetchone()
            return result['count'] if result else 0

    def get_admin_count(self) -> int:
        """Получить количество администраторов"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
            result = cursor.fetchone()
            return result['count'] if result else 0

    def get_all_users(self) -> List[User]:
        """Получить всех пользователей (алиас для find_all)"""
        return self.find_all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID (алиас для find_by_id)"""
        return self.find_by_id(user_id)

    def update_user(self, user_id: int, data: dict) -> bool:
        """Обновить пользователя по данным из словаря"""
        with self.db.cursor() as cursor:
            # Строим запрос динамически
            set_clauses = []
            values = []

            # Разрешенные поля для обновления
            allowed_fields = ['email', 'is_active', 'role']

            for field in allowed_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    values.append(data[field])

            if not set_clauses:
                return False

            # Добавляем updated_at
            set_clauses.append("updated_at = NOW()")
            values.append(user_id)

            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
            cursor.execute(query, values)
            return cursor.rowcount > 0

    def _row_to_user(self, row: dict) -> User:
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            is_active=row.get('is_active', True),
            role=row.get('role', 'user'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
