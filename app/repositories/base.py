from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseRepository(ABC):
    """Базовый репозиторий с общими методами"""
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def find_all(self) -> List[Any]:
        pass

    @abstractmethod
    def create(self, entity: Any) -> int:
        pass

    @abstractmethod
    def update(self, entity: Any) -> bool:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
