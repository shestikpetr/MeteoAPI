"""
Admin Panel Services
Бизнес-логика для административной панели
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.repositories.user_repository import UserRepository
from app.repositories.station_repository import StationRepository
from app.database.connection import DatabaseManager
from app.config import Config


class AdminService:
    """Сервис для административной панели"""

    def __init__(self):
        self.user_repo = UserRepository()
        self.station_repo = StationRepository()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получить статистику для dashboard"""
        try:
            # Получаем статистику пользователей
            total_users = self.user_repo.get_user_count()
            active_users = self.user_repo.get_active_user_count()
            admin_users = self.user_repo.get_admin_count()

            # Получаем статистику станций
            total_stations = self.station_repo.get_station_count()
            active_stations = self.station_repo.get_active_station_count()

            # Получаем статистику подключений к БД
            db_stats = DatabaseManager.get_connection_stats()

            # Формируем результат
            stats = {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'admins': admin_users,
                    'inactive': total_users - active_users
                },
                'stations': {
                    'total': total_stations,
                    'active': active_stations,
                    'inactive': total_stations - active_stations
                },
                'database': db_stats,
                'system': {
                    'connection_pooling': Config.USE_CONNECTION_POOLING,
                    'uptime': self._get_system_uptime(),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

            return stats

        except Exception as e:
            print(f"Ошибка получения статистики dashboard: {e}")
            return {}

    def get_user_management_data(self) -> Dict[str, Any]:
        """Получить данные для управления пользователями"""
        try:
            users = self.user_repo.get_all_users()
            users_data = []

            for user in users:
                user_stations = self.station_repo.get_user_stations(user.id)
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
                    'stations_count': len(user_stations)
                })

            return {
                'users': users_data,
                'total_count': len(users_data)
            }

        except Exception as e:
            print(f"Ошибка получения данных пользователей: {e}")
            return {'users': [], 'total_count': 0}

    def get_station_management_data(self) -> Dict[str, Any]:
        """Получить данные для управления станциями"""
        try:
            stations = self.station_repo.get_all_stations()
            stations_data = []

            for station in stations:
                # Получаем параметры станции
                parameters = self.station_repo.get_station_parameters(station.id)

                stations_data.append({
                    'id': station.id,
                    'station_number': station.station_number,
                    'name': station.name,
                    'location': station.location,
                    'latitude': station.latitude,
                    'longitude': station.longitude,
                    'altitude': station.altitude,
                    'is_active': station.is_active,
                    'created_at': station.created_at.strftime('%Y-%m-%d %H:%M:%S') if station.created_at else None,
                    'parameters_count': len(parameters)
                })

            return {
                'stations': stations_data,
                'total_count': len(stations_data)
            }

        except Exception as e:
            print(f"Ошибка получения данных станций: {e}")
            return {'stations': [], 'total_count': 0}

    def get_system_monitoring_data(self) -> Dict[str, Any]:
        """Получить данные мониторинга системы"""
        try:
            # Статистика подключений к БД
            db_stats = DatabaseManager.get_connection_stats()

            # Системная информация
            system_info = {
                'connection_pooling': Config.USE_CONNECTION_POOLING,
                'pool_settings': {
                    'min_connections': Config.DB_POOL_MIN_CONNECTIONS,
                    'max_connections': Config.DB_POOL_MAX_CONNECTIONS,
                    'max_idle_time': Config.DB_POOL_MAX_IDLE_TIME,
                    'connection_timeout': Config.DB_CONNECTION_TIMEOUT
                } if Config.USE_CONNECTION_POOLING else None,
                'redis_settings': {
                    'host': Config.REDIS_HOST,
                    'port': Config.REDIS_PORT,
                    'db': Config.REDIS_DB,
                    'cache_ttl': Config.CACHE_TTL
                }
            }

            return {
                'database': db_stats,
                'system': system_info,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            print(f"Ошибка получения данных мониторинга: {e}")
            return {}

    def _get_system_uptime(self) -> str:
        """Получить время работы системы (примерное)"""
        try:
            # Это упрощенная версия - в реальности можно отслеживать время запуска
            return "Система работает"
        except:
            return "Неизвестно"


class UserManagementService:
    """Сервис для управления пользователями"""

    def __init__(self):
        self.user_repo = UserRepository()

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать нового пользователя"""
        try:
            from app.services.auth_service_fastapi import AuthServiceFastAPI
            auth_service = AuthServiceFastAPI()

            # Создаем пользователя через auth сервис
            result = auth_service.register(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                role=user_data.get('role', 'user')
            )

            return {'success': True, 'user': result}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить пользователя"""
        try:
            # Получаем существующего пользователя
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'Пользователь не найден'}

            # Обновляем данные
            updated = self.user_repo.update_user(user_id, user_data)

            if updated:
                return {'success': True, 'message': 'Пользователь обновлен'}
            else:
                return {'success': False, 'error': 'Ошибка обновления пользователя'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Удалить пользователя (деактивировать)"""
        try:
            # Деактивируем пользователя вместо удаления
            updated = self.user_repo.update_user(user_id, {'is_active': False})

            if updated:
                return {'success': True, 'message': 'Пользователь деактивирован'}
            else:
                return {'success': False, 'error': 'Ошибка деактивации пользователя'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


class StationManagementService:
    """Сервис для управления станциями"""

    def __init__(self):
        self.station_repo = StationRepository()

    def create_station(self, station_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новую станцию"""
        try:
            station_id = self.station_repo.create_station(station_data)

            if station_id:
                return {'success': True, 'station_id': station_id}
            else:
                return {'success': False, 'error': 'Ошибка создания станции'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_station(self, station_id: int, station_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить станцию"""
        try:
            updated = self.station_repo.update_station(station_id, station_data)

            if updated:
                return {'success': True, 'message': 'Станция обновлена'}
            else:
                return {'success': False, 'error': 'Ошибка обновления станции'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_station(self, station_id: int) -> Dict[str, Any]:
        """Удалить станцию (деактивировать)"""
        try:
            # Деактивируем станцию вместо удаления
            updated = self.station_repo.update_station(station_id, {'is_active': False})

            if updated:
                return {'success': True, 'message': 'Станция деактивирована'}
            else:
                return {'success': False, 'error': 'Ошибка деактивации станции'}

        except Exception as e:
            return {'success': False, 'error': str(e)}