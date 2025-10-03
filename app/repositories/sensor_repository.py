from typing import List, Dict, Optional
from app.database.connection import DatabaseManager
from app.models.parameter import SensorData


class SensorRepository:
    """Репозиторий для работы с данными датчиков"""

    def __init__(self):
        self.db = DatabaseManager.get_sensor_db()

    def get_latest_value(self, station_number: str, parameter: str) -> Optional[float]:
        """Получить последнее значение параметра"""
        with self.db.cursor() as cursor:
            # Проверяем существование таблицы
            cursor.execute("SHOW TABLES LIKE %s", (station_number,))
            if not cursor.fetchone():
                return None

            # Проверяем существование колонки
            cursor.execute(
                f"SHOW COLUMNS FROM `{station_number}` LIKE %s",
                (parameter,)
            )
            if not cursor.fetchone():
                return None

            # Получаем последнее значение
            query = f"""
                SELECT `{parameter}` as value 
                FROM `{station_number}` 
                WHERE `{parameter}` > -100 
                ORDER BY time DESC 
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()

            return float(result['value']) if result and result['value'] is not None else None

    def get_time_series(self, station_number: str, parameter: str,
                        start_time: int = None, end_time: int = None,
                        limit: int = None) -> List[SensorData]:
        """Получить временной ряд данных"""
        with self.db.cursor() as cursor:
            # Проверяем существование таблицы и колонки
            cursor.execute("SHOW TABLES LIKE %s", (station_number,))
            if not cursor.fetchone():
                return []

            cursor.execute(
                f"SHOW COLUMNS FROM `{station_number}` LIKE %s",
                (parameter,)
            )
            if not cursor.fetchone():
                return []

            # Формируем запрос
            query = f"""
                SELECT time, `{parameter}` as value 
                FROM `{station_number}` 
                WHERE `{parameter}` > -100
            """
            params = []

            if start_time:
                query += " AND time >= %s"
                params.append(start_time)

            if end_time:
                query += " AND time <= %s"
                params.append(end_time)

            query += " ORDER BY time DESC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [
                SensorData(
                    time=row['time'],
                    value=float(row['value']),
                    parameter=parameter,
                    station=station_number
                )
                for row in results
                if row['value'] is not None
            ]

    def get_available_parameters(self, station_number: str) -> List[str]:
        """Получить список доступных параметров станции"""
        with self.db.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", (station_number,))
            if not cursor.fetchone():
                return []

            cursor.execute(f"SHOW COLUMNS FROM `{station_number}`")
            columns = cursor.fetchall()

            # Исключаем служебную колонку time
            return [
                col['Field'] for col in columns
                if col['Field'] != 'time'
            ]

    def get_multiple_latest(self, station_number: str, parameters: List[str]) -> Dict[str, Optional[float]]:
        """Получить последние значения нескольких параметров"""
        result = {}

        with self.db.cursor() as cursor:
            # Проверяем существование таблицы
            cursor.execute("SHOW TABLES LIKE %s", (station_number,))
            if not cursor.fetchone():
                return {param: None for param in parameters}

            # Получаем данные для каждого параметра
            for param in parameters:
                cursor.execute(
                    f"SHOW COLUMNS FROM `{station_number}` LIKE %s",
                    (param,)
                )
                if not cursor.fetchone():
                    result[param] = None
                    continue

                query = f"""
                    SELECT `{param}` as value 
                    FROM `{station_number}` 
                    WHERE `{param}` > -100 
                    ORDER BY time DESC 
                    LIMIT 1
                """
                cursor.execute(query)
                row = cursor.fetchone()

                result[param] = float(
                    row['value']) if row and row['value'] is not None else None

        return result
