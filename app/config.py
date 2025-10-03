import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration for FastAPI application"""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # API Settings
    API_TITLE = "MeteoApp FastAPI"
    API_VERSION = "2.0.0"
    API_DESCRIPTION = "REST API for meteorological data management"

    # CORS
    CORS_ORIGINS = ["*"]  # Configure for production

    # Local Database (MySQL)
    LOCAL_DB_HOST = os.environ.get('LOCAL_DB_HOST', 'localhost')
    LOCAL_DB_PORT = int(os.environ.get('LOCAL_DB_PORT', 3306))
    LOCAL_DB_USER = os.environ.get('LOCAL_DB_USER', 'root')
    LOCAL_DB_PASSWORD = os.environ.get('LOCAL_DB_PASSWORD', '')
    LOCAL_DB_NAME = os.environ.get('LOCAL_DB_NAME', 'meteo_local')

    # Remote Sensor Database
    SENSOR_DB_HOST = os.environ.get('SENSOR_DB_HOST', '')
    SENSOR_DB_PORT = int(os.environ.get('SENSOR_DB_PORT', 3306))
    SENSOR_DB_USER = os.environ.get('SENSOR_DB_USER', '')
    SENSOR_DB_PASSWORD = os.environ.get('SENSOR_DB_PASSWORD', '')
    SENSOR_DB_NAME = os.environ.get('SENSOR_DB_NAME', '')

    # Redis for caching
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))  # 5 minutes

    # Database Connection Pooling
    USE_CONNECTION_POOLING = os.environ.get('USE_CONNECTION_POOLING', 'true').lower() == 'true'
    DB_POOL_MIN_CONNECTIONS = int(os.environ.get('DB_POOL_MIN_CONNECTIONS', 3))
    DB_POOL_MAX_CONNECTIONS = int(os.environ.get('DB_POOL_MAX_CONNECTIONS', 15))
    DB_POOL_MAX_IDLE_TIME = int(os.environ.get('DB_POOL_MAX_IDLE_TIME', 3600))  # 1 hour
    DB_CONNECTION_TIMEOUT = int(os.environ.get('DB_CONNECTION_TIMEOUT', 30))  # 30 seconds

    @property
    def local_db_url(self):
        """Get local database URL for PyMySQL"""
        return f"mysql+pymysql://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}/{self.LOCAL_DB_NAME}"

    @property
    def sensor_db_url(self):
        """Get sensor database URL for PyMySQL"""
        return f"mysql+pymysql://{self.SENSOR_DB_USER}:{self.SENSOR_DB_PASSWORD}@{self.SENSOR_DB_HOST}:{self.SENSOR_DB_PORT}/{self.SENSOR_DB_NAME}"


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"


# Configuration selector
def get_config():
    env = os.environ.get('ENVIRONMENT', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()