from typing import List, Dict, Optional
from app.models.station import Station
from app.repositories.station_repository import StationRepository
from app.repositories.sensor_repository import SensorRepository
from app.repositories.parameter_visibility_repository import ParameterVisibilityRepository
from app.services.access_control_service import AccessControlService
from app.utils.validators import Validators
from app.utils.exceptions import ValidationError, NotFoundError, ConflictError


class StationManagementService:
    """Сервис для управления станциями пользователя

    Single Responsibility: CRUD операции со станциями пользователя
    """

    def __init__(self,
                 station_repo: Optional[StationRepository] = None,
                 sensor_repo: Optional[SensorRepository] = None,
                 visibility_repo: Optional[ParameterVisibilityRepository] = None,
                 access_service: Optional[AccessControlService] = None,
                 validators: Optional[Validators] = None):
        """Dependency Injection"""
        self.station_repo = station_repo or StationRepository()
        self.sensor_repo = sensor_repo or SensorRepository()
        self.visibility_repo = visibility_repo or ParameterVisibilityRepository()
        self.access_service = access_service or AccessControlService()
        self.validators = validators or Validators()

    def add_user_station(self, user_id: str, station_number: str,
                         custom_name: str = None) -> Optional[Dict]:
        """Добавить станцию пользователю

        Args:
            user_id: ID пользователя (строка)
            station_number: номер станции (8 цифр)
            custom_name: пользовательское название станции

        Returns:
            dict с информацией о добавленной станции или None если станция не существует
        """
        user_id_int = int(user_id)

        # Валидация номера станции
        if not self.validators.validate_station_number(station_number):
            raise ValidationError("Некорректный номер станции (должен содержать 8 цифр)")

        # Проверяем существование станции в БД датчиков
        if not self.station_repo.check_station_exists_in_sensor_db(station_number):
            return None

        # Проверяем, не добавлена ли уже станция пользователю
        if self.access_service.check_user_has_station(user_id_int, station_number):
            raise ConflictError("Станция уже добавлена")

        # Проверяем/создаем станцию в локальной БД
        station = self.station_repo.find_by_number(station_number)
        if not station:
            station = Station(
                station_number=station_number,
                name=custom_name or f"Станция {station_number}",
                is_active=True
            )
            station_id = self.station_repo.create(station)
            station.id = station_id

            # Синхронизируем параметры станции
            self._sync_station_parameters(station_id, station_number)
        else:
            station_id = station.id

        # Добавляем станцию пользователю
        user_station_id = self.station_repo.add_user_station(
            user_id_int, station_id, custom_name
        )

        # Инициализируем видимость параметров (все видимы по умолчанию)
        available_parameters = self.sensor_repo.get_available_parameters(station_number)
        self.visibility_repo.initialize_parameters_for_user_station(
            user_station_id, available_parameters
        )

        return {
            'user_station_id': user_station_id,
            'station_number': station_number,
            'custom_name': custom_name or station.name,
            'parameters_count': len(available_parameters)
        }

    def remove_user_station(self, user_id: str, station_number: str) -> bool:
        """Удалить станцию у пользователя"""
        user_id_int = int(user_id)

        station = self.station_repo.find_by_number(station_number)
        if not station:
            raise NotFoundError("Станция не найдена")

        success = self.station_repo.remove_user_station(user_id_int, station.id)
        if not success:
            raise NotFoundError("Станция не найдена у пользователя")

        return True

    def update_user_station(self, user_id: str, station_number: str,
                            custom_name: str = None, is_favorite: bool = None) -> bool:
        """Обновить настройки станции пользователя"""
        user_id_int = int(user_id)

        # Проверяем доступ и получаем user_station_id
        user_station_id = self.access_service.verify_access_to_station(
            user_id_int, station_number
        )

        # Обновляем настройки
        return self.station_repo.update_user_station(
            user_station_id,
            custom_name=custom_name,
            is_favorite=is_favorite
        )

    def get_user_stations(self, user_id: str) -> List[Dict]:
        """Получить все станции пользователя

        Returns:
            список станций в формате для UserStationResponse
        """
        user_id_int = int(user_id)
        stations = self.station_repo.get_user_stations(user_id_int)

        result = []
        for station_data in stations:
            user_station = {
                'id': str(station_data['user_station_id']),
                'user_id': user_id,
                'station_id': str(station_data['id']),
                'custom_name': station_data.get('custom_name'),
                'is_favorite': bool(station_data.get('is_favorite', False)),
                'created_at': station_data.get('created_at'),
                'station': {
                    'id': str(station_data['id']),
                    'station_number': station_data['station_number'],
                    'name': station_data['name'],
                    'location': station_data.get('location'),
                    'latitude': station_data.get('latitude'),
                    'longitude': station_data.get('longitude'),
                    'altitude': station_data.get('altitude'),
                    'is_active': bool(station_data.get('is_active', True)),
                    'created_at': station_data.get('created_at'),
                    'updated_at': station_data.get('updated_at')
                }
            }
            result.append(user_station)

        return result

    def _sync_station_parameters(self, station_id: int, station_number: str):
        """Синхронизировать параметры станции с БД датчиков"""
        try:
            parameters = self.sensor_repo.get_available_parameters(station_number)

            if not parameters:
                print(f"Параметры для станции {station_number} не найдены в БД датчиков")
                return

            added_count = self.station_repo.sync_station_parameters(station_id, parameters)
            print(f"Синхронизировано {added_count} параметров для станции {station_number}")

        except Exception as e:
            print(f"Ошибка синхронизации параметров для станции {station_number}: {e}")