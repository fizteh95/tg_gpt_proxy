from abc import ABC
from abc import abstractmethod

from src.domain.models import AccessCounter
from src.domain.models import Context
from src.domain.models import TgUser


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

    @abstractmethod
    async def create_tg_user(self, tg_user: TgUser) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_tg_user(self, chat_id: str) -> TgUser | None:
        raise NotImplementedError

    @abstractmethod
    async def change_tg_user_state(
        self, chat_id: str, state_map: str, state: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_tg_user_state(self, chat_id: str) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def get_access_counter(self, user_id: str) -> AccessCounter | None:
        raise NotImplementedError

    @abstractmethod
    async def set_access_counter_usual_for_everybody(self, count_level: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def set_access_counter(
        self, user_id: str, access_counter: AccessCounter
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def save_out_tg_message(
        self,
        chat_id: str,
        text: str,
        text_like: str,
        message_id: str,
        not_pushed_to_delete: bool,
        not_pushed_to_edit_text: str = "",
        pushed: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def make_saved_message_pushed(
        self, chat_id: str, message_text_like: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_exist_not_pushed_message_to_delete(self, chat_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def get_exist_not_pushed_message_to_edit(
        self, chat_id: str
    ) -> tuple[str, str, str] | tuple[None, None, None]:
        raise NotImplementedError

    @abstractmethod
    async def remove_out_tg_message(self, chat_id: str, message_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_saved_tg_message(
        self, chat_id: str, text_like: str
    ) -> tuple[str, str, str]:
        raise NotImplementedError
