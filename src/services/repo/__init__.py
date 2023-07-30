from abc import ABC
from abc import abstractmethod

from src.domain.models import Context


class AbstractRepo(ABC):
    @abstractmethod
    async def prepare_db(self) -> None:
        """Migrations, etc"""

    @abstractmethod
    async def save_context(self, user_id: str, context: Context) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_context(self, user_id: str) -> Context | None:
        raise NotImplementedError

    @abstractmethod
    async def clear_context(self, user_id: str) -> None:
        raise NotImplementedError
