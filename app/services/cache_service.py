import json
import redis
from typing import Optional, Any
from app.config import Config


class CacheService:
    """Сервис кэширования с использованием Redis"""

    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            self.enabled = True
        except:
            self.redis_client = None
            self.enabled = False
            print("Redis недоступен, кэширование отключено")

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if not self.enabled:
            return None

        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Сохранить значение в кэш"""
        if not self.enabled:
            return False

        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except:
            return False

    def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        if not self.enabled:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except:
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Очистить все ключи по паттерну"""
        if not self.enabled:
            return False

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except:
            return False
