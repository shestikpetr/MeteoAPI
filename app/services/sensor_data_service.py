from typing import List, Dict, Optional
from datetime import datetime
from app.repositories.sensor_repository import SensorRepository
from app.repositories.station_repository import StationRepository
from app.repositories.parameter_visibility_repository import ParameterVisibilityRepository
from app.services.access_control_service import AccessControlService
from app.utils.exceptions import NotFoundError, ValidationError


class SensorDataService:
    """Сервис для получения данных с датчиков

    Single Responsibility: только получение и форматирование данных датчиков
    Не проверяет доступ - делегирует AccessControlService
    """

    def __init__(self,
                 sensor_repo: Optional[SensorRepository] = None,
                 station_repo: Optional[StationRepository] = None,
                 visibility_repo: Optional[ParameterVisibilityRepository] = None,
                 access_service: Optional[AccessControlService] = None):
        """Dependency Injection"""
        self.sensor_repo = sensor_repo or SensorRepository()
        self.station_repo = station_repo or StationRepository()
        self.visibility_repo = visibility_repo or ParameterVisibilityRepository()
        self.access_service = access_service or AccessControlService()

    def get_station_latest_data(self, user_id: str, station_number: str) -> Dict:
        """Получить последние данные станции (только видимые параметры)

        Args:
            user_id: ID пользователя (строка)
            station_number: номер станции

        Returns:
            dict с последними значениями видимых параметров
        """
        user_id_int = int(user_id)

        # Проверяем доступ и получаем информацию о станции
        station_info = self.access_service.get_user_station_info(user_id_int, station_number)
        if not station_info:
            raise NotFoundError("Станция не найдена или нет доступа")

        user_station_id = station_info['user_station_id']

        # Получаем видимые параметры
        visible_params = self.visibility_repo.get_visible_parameters(user_station_id)

        if not visible_params:
            return {
                'station_number': station_number,
                'custom_name': station_info.get('custom_name') or station_info['name'],
                'is_favorite': bool(station_info.get('is_favorite', False)),
                'location': station_info.get('location'),
                'latitude': station_info.get('latitude'),
                'longitude': station_info.get('longitude'),
                'parameters': [],
                'timestamp': datetime.now().isoformat()
            }

        # Получаем данные параметров
        values = self.sensor_repo.get_multiple_latest(station_number, visible_params)

        # Получаем информацию о параметрах
        param_info = self._get_parameters_info(visible_params)

        # Форматируем ответ
        parameters = []
        for param_code in visible_params:
            info = param_info.get(param_code, {})
            parameters.append({
                'code': param_code,
                'name': info.get('name', f'Параметр {param_code}'),
                'value': values.get(param_code),
                'unit': info.get('unit', ''),
                'category': info.get('category', 'other')
            })

        return {
            'station_number': station_number,
            'custom_name': station_info.get('custom_name') or station_info['name'],
            'is_favorite': bool(station_info.get('is_favorite', False)),
            'location': station_info.get('location'),
            'latitude': station_info.get('latitude'),
            'longitude': station_info.get('longitude'),
            'parameters': parameters,
            'timestamp': datetime.now().isoformat()
        }

    def get_all_stations_latest_data(self, user_id: str) -> List[Dict]:
        """Получить последние данные всех станций пользователя

        Для мобилки: один запрос возвращает все станции с их последними данными
        """
        user_id_int = int(user_id)

        # Получаем все станции пользователя
        user_stations = self.station_repo.get_user_stations(user_id_int)

        if not user_stations:
            return []

        result = []

        for station in user_stations:
            station_number = station['station_number']
            user_station_id = station['user_station_id']

            # Получаем видимые параметры
            visible_params = self.visibility_repo.get_visible_parameters(user_station_id)

            if not visible_params:
                # Станция без видимых параметров - пропускаем или добавляем пустую
                result.append({
                    'station_number': station_number,
                    'custom_name': station.get('custom_name') or station['name'],
                    'is_favorite': bool(station.get('is_favorite', False)),
                    'location': station.get('location'),
                    'latitude': station.get('latitude'),
                    'longitude': station.get('longitude'),
                    'parameters': []
                })
                continue

            # Получаем данные параметров
            try:
                values = self.sensor_repo.get_multiple_latest(station_number, visible_params)
                param_info = self._get_parameters_info(visible_params)

                parameters = []
                for param_code in visible_params:
                    info = param_info.get(param_code, {})
                    value = values.get(param_code)

                    # Добавляем параметр только если есть значение
                    if value is not None:
                        parameters.append({
                            'code': param_code,
                            'name': info.get('name', f'Параметр {param_code}'),
                            'value': value,
                            'unit': info.get('unit', ''),
                            'category': info.get('category', 'other')
                        })

                result.append({
                    'station_number': station_number,
                    'custom_name': station.get('custom_name') or station['name'],
                    'is_favorite': bool(station.get('is_favorite', False)),
                    'location': station.get('location'),
                    'latitude': station.get('latitude'),
                    'longitude': station.get('longitude'),
                    'parameters': parameters
                })

            except Exception as e:
                print(f"Ошибка получения данных станции {station_number}: {e}")
                # Пропускаем станцию при ошибке
                continue

        return result

    def get_parameter_history(self, user_id: str, station_number: str,
                              parameter_code: str, start_time: int = None,
                              end_time: int = None, limit: int = 1000) -> Dict:
        """Получить исторические данные параметра

        Args:
            user_id: ID пользователя
            station_number: номер станции
            parameter_code: код параметра
            start_time: начало периода (unix timestamp)
            end_time: конец периода (unix timestamp)
            limit: максимальное количество записей

        Returns:
            dict с временным рядом данных
        """
        user_id_int = int(user_id)

        # Проверяем доступ
        user_station_id = self.access_service.verify_access_to_station(
            user_id_int, station_number
        )

        # Проверяем видимость параметра
        if not self.visibility_repo.check_parameter_visible(user_station_id, parameter_code):
            raise NotFoundError(
                f"Параметр {parameter_code} не найден или скрыт")

        # Валидация лимита
        if limit > 10000:
            raise ValidationError("Лимит не может превышать 10000 записей")

        # Получаем данные
        data = self.sensor_repo.get_time_series(
            station_number, parameter_code, start_time, end_time, limit
        )

        if not data:
            raise NotFoundError(f"Данные не найдены для параметра {parameter_code}")

        # Получаем информацию о параметре
        param_info = self._get_parameter_info(parameter_code)

        return {
            'station_number': station_number,
            'parameter': {
                'code': parameter_code,
                'name': param_info.get('name', f'Параметр {parameter_code}'),
                'unit': param_info.get('unit', ''),
                'category': param_info.get('category', 'other')
            },
            'data': [
                {
                    'time': d.time,
                    'value': d.value
                }
                for d in data
            ],
            'count': len(data)
        }

    def _get_parameters_info(self, parameter_codes: List[str]) -> Dict[str, Dict]:
        """Получить информацию о параметрах из локальной БД

        Returns:
            dict {parameter_code: {name, unit, description, category}}
        """
        if not parameter_codes:
            return {}

        with self.station_repo.db.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(parameter_codes))
            cursor.execute(
                f"SELECT code, name, unit, description, category FROM parameters WHERE code IN ({placeholders})",
                parameter_codes
            )
            rows = cursor.fetchall()

            return {
                row['code']: {
                    'name': row['name'],
                    'unit': row.get('unit', ''),
                    'description': row.get('description', ''),
                    'category': row.get('category', 'other')
                }
                for row in rows
            }

    def _get_parameter_info(self, parameter_code: str) -> Dict:
        """Получить информацию об одном параметре"""
        info = self._get_parameters_info([parameter_code])
        return info.get(parameter_code, {})