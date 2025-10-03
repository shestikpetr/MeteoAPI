from typing import Optional, List, Dict
from app.repositories.base import BaseRepository
from app.models.station import Station, UserStation, StationParameter
from app.database.connection import DatabaseManager


class StationRepository(BaseRepository):
    """Репозиторий для работы со станциями"""

    def __init__(self):
        self.db = DatabaseManager.get_local_db()

    def find_by_id(self, id: int) -> Optional[Station]:
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM stations WHERE id = %s", (id,))
            row = cursor.fetchone()
            return self._row_to_station(row) if row else None

    def find_by_number(self, station_number: str) -> Optional[Station]:
        with self.db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM stations WHERE station_number = %s",
                (station_number,)
            )
            row = cursor.fetchone()
            return self._row_to_station(row) if row else None

    def find_all(self) -> List[Station]:
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM stations")
            rows = cursor.fetchall()
            return [self._row_to_station(row) for row in rows]

    def create(self, station: Station) -> int:
        with self.db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO stations 
                (station_number, name, location, latitude, longitude, altitude, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
                (station.station_number, station.name, station.location,
                 station.latitude, station.longitude, station.altitude, station.is_active)
            )
            return cursor.lastrowid

    def update(self, station: Station) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute(
                """UPDATE stations 
                SET name = %s, location = %s, latitude = %s, longitude = %s, 
                    altitude = %s, is_active = %s, updated_at = NOW()
                WHERE id = %s""",
                (station.name, station.location, station.latitude,
                 station.longitude, station.altitude, station.is_active, station.id)
            )
            return cursor.rowcount > 0

    def delete(self, id: int) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute("DELETE FROM stations WHERE id = %s", (id,))
            return cursor.rowcount > 0

    def get_user_stations(self, user_id: int) -> List[Dict]:
        """Получить все станции пользователя"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """SELECT s.*, us.custom_name, us.is_favorite, us.id as user_station_id
                FROM stations s
                JOIN user_stations us ON s.id = us.station_id
                WHERE us.user_id = %s
                ORDER BY us.is_favorite DESC, us.created_at DESC""",
                (user_id,)
            )
            return cursor.fetchall()

    def add_user_station(self, user_id: int, station_id: int, custom_name: str = None) -> int:
        """Добавить станцию пользователю"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO user_stations (user_id, station_id, custom_name, created_at)
                VALUES (%s, %s, %s, NOW())""",
                (user_id, station_id, custom_name)
            )
            return cursor.lastrowid

    def update_user_station(self, user_station_id: int, custom_name: str = None, is_favorite: bool = None) -> bool:
        """Обновить пользовательские настройки станции"""
        updates = []
        params = []

        if custom_name is not None:
            updates.append("custom_name = %s")
            params.append(custom_name)

        if is_favorite is not None:
            updates.append("is_favorite = %s")
            params.append(is_favorite)

        if not updates:
            return False

        params.append(user_station_id)

        with self.db.cursor() as cursor:
            cursor.execute(
                f"UPDATE user_stations SET {', '.join(updates)} WHERE id = %s",
                params
            )
            return cursor.rowcount > 0

    def remove_user_station(self, user_id: int, station_id: int) -> bool:
        """Удалить станцию у пользователя"""
        with self.db.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_stations WHERE user_id = %s AND station_id = %s",
                (user_id, station_id)
            )
            return cursor.rowcount > 0

    def get_station_parameters(self, station_id: int) -> List[Dict]:
        """Получить параметры станции"""
        with self.db.cursor() as cursor:
            cursor.execute(
                """SELECT sp.*, p.name, p.unit, p.description, p.category
                FROM station_parameters sp
                JOIN parameters p ON sp.parameter_code = p.code
                WHERE sp.station_id = %s AND sp.is_active = 1""",
                (station_id,)
            )
            return cursor.fetchall()

    def check_station_exists_in_sensor_db(self, station_number: str) -> bool:
        """Проверить существование станции в БД датчиков"""
        sensor_db = DatabaseManager.get_sensor_db()
        with sensor_db.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", (station_number,))
            return cursor.fetchone() is not None

    def ensure_parameter_exists(self, parameter_code: str) -> bool:
        """Убедиться что параметр существует в таблице parameters"""
        with self.db.cursor() as cursor:
            # Проверяем существование параметра
            cursor.execute("SELECT id FROM parameters WHERE code = %s", (parameter_code,))
            if cursor.fetchone():
                return True

            # Если параметра нет, создаем его с базовой информацией
            cursor.execute(
                """INSERT INTO parameters (code, name, category)
                VALUES (%s, %s, %s)""",
                (parameter_code, f"Параметр {parameter_code}", "sensor")
            )
            return True

    def add_station_parameter(self, station_id: int, parameter_code: str) -> bool:
        """Добавить параметр к станции"""
        with self.db.cursor() as cursor:
            # Убеждаемся что параметр существует
            self.ensure_parameter_exists(parameter_code)

            # Добавляем связь станция-параметр (ON DUPLICATE KEY UPDATE для избежания дублей)
            cursor.execute(
                """INSERT INTO station_parameters (station_id, parameter_code, is_active)
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE is_active = TRUE""",
                (station_id, parameter_code)
            )
            return cursor.rowcount > 0

    def sync_station_parameters(self, station_id: int, parameter_codes: List[str]) -> int:
        """Синхронизировать параметры станции"""
        added_count = 0

        for parameter_code in parameter_codes:
            if self.add_station_parameter(station_id, parameter_code):
                added_count += 1

        return added_count

    def get_station_count(self) -> int:
        """Получить общее количество станций"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM stations")
            result = cursor.fetchone()
            return result['count'] if result else 0

    def get_active_station_count(self) -> int:
        """Получить количество активных станций"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM stations WHERE is_active = 1")
            result = cursor.fetchone()
            return result['count'] if result else 0

    def get_all_stations(self) -> List[Station]:
        """Получить все станции (алиас для find_all)"""
        return self.find_all()

    def create_station(self, station_data: dict) -> int:
        """Создать станцию из словаря данных"""
        station = Station(
            station_number=station_data['station_number'],
            name=station_data['name'],
            location=station_data.get('location'),
            latitude=station_data.get('latitude'),
            longitude=station_data.get('longitude'),
            altitude=station_data.get('altitude'),
            is_active=station_data.get('is_active', True)
        )
        return self.create(station)

    def update_station(self, station_id: int, data: dict) -> bool:
        """Обновить станцию по данным из словаря"""
        with self.db.cursor() as cursor:
            # Строим запрос динамически
            set_clauses = []
            values = []

            # Разрешенные поля для обновления
            allowed_fields = ['name', 'location', 'latitude', 'longitude', 'altitude', 'is_active']

            for field in allowed_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    values.append(data[field])

            if not set_clauses:
                return False

            # Добавляем updated_at
            set_clauses.append("updated_at = NOW()")
            values.append(station_id)

            query = f"UPDATE stations SET {', '.join(set_clauses)} WHERE id = %s"
            cursor.execute(query, values)
            return cursor.rowcount > 0

    def _row_to_station(self, row: dict) -> Station:
        return Station(
            id=row['id'],
            station_number=row['station_number'],
            name=row['name'],
            location=row.get('location'),
            latitude=row.get('latitude'),
            longitude=row.get('longitude'),
            altitude=row.get('altitude'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
