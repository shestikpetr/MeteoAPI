from typing import List, Dict, Optional
from app.repositories.base import BaseRepository
from app.database.connection import DatabaseManager


class ParameterVisibilityRepository(BaseRepository):
    """Репозиторий для управления видимостью параметров пользователя"""

    def __init__(self):
        self.db = DatabaseManager.get_local_db()

    def find_by_id(self, id: int) -> Optional[Dict]:
        """Получить запись по ID"""
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_station_parameters WHERE id = %s",
                (id,)
            )
            return cursor.fetchone()

    def find_all(self) -> List[Dict]:
        """Получить все записи (обычно не используется)"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM user_station_parameters")
            return cursor.fetchall()

    def create(self, user_station_id: int, parameter_code: str,
               is_visible: bool = True, display_order: int = 0) -> int:
        """Создать запись о видимости параметра"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO user_station_parameters
                (user_station_id, parameter_code, is_visible, display_order)
                VALUES (%s, %s, %s, %s)""",
                (user_station_id, parameter_code, is_visible, display_order)
            )
            return cursor.lastrowid

    def update(self, id: int, is_visible: bool = None, display_order: int = None) -> bool:
        """Обновить настройки видимости"""
        updates = []
        params = []

        if is_visible is not None:
            updates.append("is_visible = %s")
            params.append(is_visible)

        if display_order is not None:
            updates.append("display_order = %s")
            params.append(display_order)

        if not updates:
            return False

        updates.append("updated_at = NOW()")
        params.append(id)

        with self.db.cursor() as cursor:
            cursor.execute(
                f"UPDATE user_station_parameters SET {', '.join(updates)} WHERE id = %s",
                params
            )
            return cursor.rowcount > 0

    def delete(self, id: int) -> bool:
        """Удалить запись"""
        with self.db.cursor() as cursor:
            cursor.execute("DELETE FROM user_station_parameters WHERE id = %s", (id,))
            return cursor.rowcount > 0

    def get_visible_parameters(self, user_station_id: int) -> List[str]:
        """Получить список видимых параметров для станции пользователя"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """SELECT parameter_code
                FROM user_station_parameters
                WHERE user_station_id = %s AND is_visible = TRUE
                ORDER BY display_order ASC, parameter_code ASC""",
                (user_station_id,)
            )
            rows = cursor.fetchall()
            return [row['parameter_code'] for row in rows]

    def get_all_parameters_with_visibility(self, user_station_id: int) -> List[Dict]:
        """Получить все параметры станции с информацией о видимости"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """SELECT usp.*, p.name, p.unit, p.description, p.category
                FROM user_station_parameters usp
                JOIN parameters p ON usp.parameter_code = p.code
                WHERE usp.user_station_id = %s
                ORDER BY usp.display_order ASC, usp.parameter_code ASC""",
                (user_station_id,)
            )
            return cursor.fetchall()

    def set_parameter_visibility(self, user_station_id: int, parameter_code: str,
                                 is_visible: bool) -> bool:
        """Изменить видимость конкретного параметра"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """UPDATE user_station_parameters
                SET is_visible = %s, updated_at = NOW()
                WHERE user_station_id = %s AND parameter_code = %s""",
                (is_visible, user_station_id, parameter_code)
            )
            return cursor.rowcount > 0

    def bulk_set_visibility(self, user_station_id: int,
                           parameters: List[Dict[str, bool]]) -> int:
        """Массовое изменение видимости параметров

        Args:
            user_station_id: ID связи пользователя со станцией
            parameters: список словарей [{"code": "4402", "visible": True}, ...]

        Returns:
            количество обновленных записей
        """
        updated_count = 0
        with self.db.cursor() as cursor:
            for param in parameters:
                cursor.execute(
                    """UPDATE user_station_parameters
                    SET is_visible = %s, updated_at = NOW()
                    WHERE user_station_id = %s AND parameter_code = %s""",
                    (param['visible'], user_station_id, param['code'])
                )
                updated_count += cursor.rowcount
        return updated_count

    def initialize_parameters_for_user_station(self, user_station_id: int,
                                                parameter_codes: List[str]) -> int:
        """Инициализировать параметры при добавлении станции пользователю

        Все параметры создаются как видимые по умолчанию
        """
        added_count = 0
        with self.db.cursor() as cursor:
            for i, parameter_code in enumerate(parameter_codes):
                cursor.execute(
                    """INSERT INTO user_station_parameters
                    (user_station_id, parameter_code, is_visible, display_order)
                    VALUES (%s, %s, TRUE, %s)
                    ON DUPLICATE KEY UPDATE is_visible = is_visible""",
                    (user_station_id, parameter_code, i)
                )
                if cursor.rowcount > 0:
                    added_count += 1
        return added_count

    def check_parameter_visible(self, user_station_id: int, parameter_code: str) -> bool:
        """Проверить видим ли параметр для пользователя"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """SELECT is_visible FROM user_station_parameters
                WHERE user_station_id = %s AND parameter_code = %s""",
                (user_station_id, parameter_code)
            )
            row = cursor.fetchone()
            return row['is_visible'] if row else False