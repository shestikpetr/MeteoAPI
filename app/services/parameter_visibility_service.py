from typing import List, Dict, Optional
from app.repositories.parameter_visibility_repository import ParameterVisibilityRepository
from app.services.access_control_service import AccessControlService
from app.utils.exceptions import NotFoundError, ValidationError


class ParameterVisibilityService:
    """Сервис для управления видимостью параметров станций

    Single Responsibility: управление настройками видимости параметров
    """

    def __init__(self,
                 visibility_repo: Optional[ParameterVisibilityRepository] = None,
                 access_service: Optional[AccessControlService] = None):
        """Dependency Injection"""
        self.visibility_repo = visibility_repo or ParameterVisibilityRepository()
        self.access_service = access_service or AccessControlService()

    def get_station_parameters(self, user_id: str, station_number: str) -> List[Dict]:
        """Получить все параметры станции с информацией о видимости

        Args:
            user_id: ID пользователя (строка)
            station_number: номер станции

        Returns:
            список параметров с полями: code, name, unit, description, category, is_visible, display_order
        """
        user_id_int = int(user_id)

        # Проверяем доступ
        user_station_id = self.access_service.verify_access_to_station(
            user_id_int, station_number
        )

        # Получаем параметры с видимостью
        parameters = self.visibility_repo.get_all_parameters_with_visibility(user_station_id)

        return [
            {
                'code': p['parameter_code'],
                'name': p['name'],
                'unit': p.get('unit', ''),
                'description': p.get('description', ''),
                'category': p.get('category', 'other'),
                'is_visible': bool(p['is_visible']),
                'display_order': p.get('display_order', 0)
            }
            for p in parameters
        ]

    def get_visible_parameters(self, user_id: str, station_number: str) -> List[str]:
        """Получить только видимые параметры станции

        Args:
            user_id: ID пользователя (строка)
            station_number: номер станции

        Returns:
            список кодов видимых параметров
        """
        user_id_int = int(user_id)

        user_station_id = self.access_service.verify_access_to_station(
            user_id_int, station_number
        )

        return self.visibility_repo.get_visible_parameters(user_station_id)

    def set_parameter_visibility(self, user_id: str, station_number: str,
                                  parameter_code: str, is_visible: bool) -> bool:
        """Изменить видимость одного параметра

        Args:
            user_id: ID пользователя (строка)
            station_number: номер станции
            parameter_code: код параметра
            is_visible: видимость (True/False)

        Returns:
            True если успешно
        """
        user_id_int = int(user_id)

        user_station_id = self.access_service.verify_access_to_station(
            user_id_int, station_number
        )

        success = self.visibility_repo.set_parameter_visibility(
            user_station_id, parameter_code, is_visible
        )

        if not success:
            raise NotFoundError(f"Параметр {parameter_code} не найден")

        return True

    def bulk_set_visibility(self, user_id: str, station_number: str,
                           parameters: List[Dict]) -> Dict:
        """Массовое изменение видимости параметров

        Args:
            user_id: ID пользователя (строка)
            station_number: номер станции
            parameters: список [{"code": "4402", "visible": True}, ...]

        Returns:
            dict с количеством обновленных параметров
        """
        user_id_int = int(user_id)

        user_station_id = self.access_service.verify_access_to_station(
            user_id_int, station_number
        )

        # Валидация
        if not parameters:
            raise ValidationError("Список параметров пуст")

        for param in parameters:
            if 'code' not in param or 'visible' not in param:
                raise ValidationError("Каждый параметр должен содержать 'code' и 'visible'")

        updated_count = self.visibility_repo.bulk_set_visibility(
            user_station_id, parameters
        )

        return {
            'updated': updated_count,
            'total': len(parameters)
        }