import pymysql
from contextlib import contextmanager
from typing import Optional, Dict, Any, Union
from app.config import Config


class DatabaseConnection:
    """Менеджер подключений к БД"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connection = None

    def connect(self):
        """Создает подключение к БД"""
        if not self._connection or not self._connection.open:
            self._connection = pymysql.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        return self._connection

    def close(self):
        """Закрывает подключение"""
        if self._connection:
            self._connection.close()
            self._connection = None

    @contextmanager
    def cursor(self):
        """Контекстный менеджер для курсора"""
        connection = self.connect()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()


class DatabaseManager:
    """Enhanced database manager with optional connection pooling"""
    _instances = {}
    _pooled_instances = {}

    @classmethod
    def get_local_db(cls) -> Union[DatabaseConnection, 'PooledDatabaseConnection']:
        """Get local database connection (pooled or single)"""
        if Config.USE_CONNECTION_POOLING:
            return cls._get_pooled_local_db()
        else:
            return cls._get_single_local_db()

    @classmethod
    def get_sensor_db(cls) -> Union[DatabaseConnection, 'PooledDatabaseConnection']:
        """Get sensor database connection (pooled or single)"""
        if Config.USE_CONNECTION_POOLING:
            return cls._get_pooled_sensor_db()
        else:
            return cls._get_single_sensor_db()

    @classmethod
    def _get_single_local_db(cls) -> DatabaseConnection:
        """Get single connection local database (legacy mode)"""
        if 'local' not in cls._instances:
            cls._instances['local'] = DatabaseConnection({
                'host': Config.LOCAL_DB_HOST,
                'port': Config.LOCAL_DB_PORT,
                'user': Config.LOCAL_DB_USER,
                'password': Config.LOCAL_DB_PASSWORD,
                'database': Config.LOCAL_DB_NAME
            })
        return cls._instances['local']

    @classmethod
    def _get_single_sensor_db(cls) -> DatabaseConnection:
        """Get single connection sensor database (legacy mode)"""
        if 'sensor' not in cls._instances:
            cls._instances['sensor'] = DatabaseConnection({
                'host': Config.SENSOR_DB_HOST,
                'port': Config.SENSOR_DB_PORT,
                'user': Config.SENSOR_DB_USER,
                'password': Config.SENSOR_DB_PASSWORD,
                'database': Config.SENSOR_DB_NAME
            })
        return cls._instances['sensor']

    @classmethod
    def _get_pooled_local_db(cls):
        """Get pooled local database connection"""
        if 'local' not in cls._pooled_instances:
            from app.database.connection_pool import PooledDatabaseConnection
            cls._pooled_instances['local'] = PooledDatabaseConnection({
                'host': Config.LOCAL_DB_HOST,
                'port': Config.LOCAL_DB_PORT,
                'user': Config.LOCAL_DB_USER,
                'password': Config.LOCAL_DB_PASSWORD,
                'database': Config.LOCAL_DB_NAME
            }, min_connections=Config.DB_POOL_MIN_CONNECTIONS,
               max_connections=Config.DB_POOL_MAX_CONNECTIONS,
               max_idle_time=Config.DB_POOL_MAX_IDLE_TIME,
               connect_timeout=Config.DB_CONNECTION_TIMEOUT)
        return cls._pooled_instances['local']

    @classmethod
    def _get_pooled_sensor_db(cls):
        """Get pooled sensor database connection"""
        if 'sensor' not in cls._pooled_instances:
            from app.database.connection_pool import PooledDatabaseConnection
            cls._pooled_instances['sensor'] = PooledDatabaseConnection({
                'host': Config.SENSOR_DB_HOST,
                'port': Config.SENSOR_DB_PORT,
                'user': Config.SENSOR_DB_USER,
                'password': Config.SENSOR_DB_PASSWORD,
                'database': Config.SENSOR_DB_NAME
            }, min_connections=max(1, Config.DB_POOL_MIN_CONNECTIONS // 2),
               max_connections=max(5, Config.DB_POOL_MAX_CONNECTIONS // 2),
               max_idle_time=Config.DB_POOL_MAX_IDLE_TIME,
               connect_timeout=Config.DB_CONNECTION_TIMEOUT)
        return cls._pooled_instances['sensor']

    @classmethod
    def close_all(cls):
        """Close all database connections and pools"""
        # Close single connections
        for name, instance in cls._instances.items():
            if hasattr(instance, 'close'):
                instance.close()
        cls._instances.clear()

        # Close pooled connections
        for name, instance in cls._pooled_instances.items():
            if hasattr(instance, 'close'):
                instance.close()
        cls._pooled_instances.clear()

    @classmethod
    def get_connection_stats(cls) -> Dict[str, Any]:
        """Get statistics for all database connections"""
        stats = {
            'pooling_enabled': Config.USE_CONNECTION_POOLING,
            'pools': {}
        }

        if Config.USE_CONNECTION_POOLING:
            for name, instance in cls._pooled_instances.items():
                if hasattr(instance, 'get_stats'):
                    stats['pools'][name] = instance.get_stats()
        else:
            stats['pools'] = {name: {'type': 'single_connection'}
                            for name in cls._instances.keys()}

        return stats
