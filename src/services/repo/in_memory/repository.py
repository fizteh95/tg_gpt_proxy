import copy

from src.domain.models import Context
from src.services.repo import AbstractRepo


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.context: dict[str, Context] = {}

    async def prepare_db(self) -> None:
        pass

    async def save_context(self, user_id: str, context: Context) -> None:
        self.context[user_id] = context

    async def get_context(self, user_id: str) -> Context | None:
        return copy.deepcopy(self.context.get(user_id))

    async def clear_context(self, user_id: str) -> None:
        try:
            self.context.pop(user_id)
        except KeyError:
            pass
