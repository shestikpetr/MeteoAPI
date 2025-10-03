from typing import Optional, Dict
from app.repositories.station_repository import StationRepository
from app.repositories.parameter_visibility_repository import ParameterVisibilityRepository


class AccessControlService:
    """Сервис для проверки прав доступа пользователя к станциям и параметрам

    Single Responsibility: только проверка доступа, без бизнес-логики
    """

    def __init__(self,
                 station_repo: Optional[StationRepository] = None,
                 visibility_repo: Optional[ParameterVisibilityRepository] = None):
        """Dependency Injection для репозиториев"""
        self.station_repo = station_repo or StationRepository()
        self.visibility_repo = visibility_repo or ParameterVisibilityRepository()

    def check_user_has_station(self, user_id: int, station_number: str) -> bool:
        """Проверить имеет ли пользователь доступ к станции"""
        user_stations = self.station_repo.get_user_stations(user_id)
        return any(us['station_number'] == station_number for us in user_stations)

    def get_user_station_id(self, user_id: int, station_number: str) -> Optional[int]:
        """Получить ID связи user_station для пользователя и станции

        Returns:
            user_station_id или None если доступа нет
        """
        user_stations = self.station_repo.get_user_stations(user_id)
        for us in user_stations:
            if us['station_number'] == station_number:
                return us['user_station_id']
        return None

    def get_user_station_info(self, user_id: int, station_number: str) -> Optional[Dict]:
        """Получить полную информацию о станции пользователя

        Returns:
            dict с полями station, custom_name, is_favorite, user_station_id и т.д.
            или None если доступа нет
        """
        user_stations = self.station_repo.get_user_stations(user_id)
        for us in user_stations:
            if us['station_number'] == station_number:
                return us
        return None

    def check_parameter_visible(self, user_station_id: int, parameter_code: str) -> bool:
        """Проверить видим ли параметр для пользователя"""
        return self.visibility_repo.check_parameter_visible(user_station_id, parameter_code)

    def verify_access_to_station(self, user_id: int, station_number: str) -> int:
        """Проверить доступ и вернуть user_station_id

        Args:
            user_id: ID пользователя
            station_number: номер станции

        Returns:
            user_station_id

        Raises:
            NotFoundError: если доступа нет
        """
        from app.utils.exceptions import NotFoundError

        user_station_id = self.get_user_station_id(user_id, station_number)
        if user_station_id is None:
            raise NotFoundError("Станция не найдена или нет доступа")

        return user_station_id