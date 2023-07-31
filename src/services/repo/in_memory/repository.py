import copy

from src.domain.models import AccessCounter
from src.domain.models import Context
from src.domain.models import TgUser
from src.services.repo import AbstractRepo


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.context: dict[str, Context] = {}
        self.tg_user: dict[str, TgUser] = {}
        self.tg_user_state: dict[str, dict[str, str]] = {}
        self.access_counter: dict[str, AccessCounter] = {}
        self.out_tg_messages: list[dict[str, str]] = []

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

    async def create_tg_user(self, tg_user: TgUser) -> None:
        self.tg_user[tg_user.chat_id] = tg_user

    async def get_tg_user(self, chat_id: str) -> TgUser | None:
        return copy.deepcopy(self.tg_user.get(chat_id))

    async def change_tg_user_state(
        self, chat_id: str, state_map: str, state: str
    ) -> None:
        if not self.tg_user_state.get(chat_id):
            self.tg_user_state[chat_id] = {}
        self.tg_user_state[chat_id][state_map] = state

    async def get_tg_user_state(self, chat_id: str) -> dict[str, str]:
        return copy.deepcopy(self.tg_user_state.get(chat_id, {}))

    async def get_access_counter(self, user_id: str) -> AccessCounter:
        return copy.deepcopy(
            self.access_counter.get(
                user_id, AccessCounter(remain_per_day=0, remain_per_all_time=0)
            )
        )

    async def set_access_counter(
        self, user_id: str, access_counter: AccessCounter
    ) -> None:
        self.access_counter[user_id] = access_counter

    async def save_out_tg_message(
        self, chat_id: str, text: str, text_like: str, message_id: str
    ) -> None:
        self.out_tg_messages.append(
            dict(chat_id=chat_id, text=text, text_like=text_like, message_id=message_id)
        )

    async def get_saved_tg_message(
        self, chat_id: str, text_like: str
    ) -> tuple[str, str]:
        for item in self.out_tg_messages[::-1]:
            if item["chat_id"] == chat_id and item["text_like"] == text_like:
                return item["text"], item["message_id"]
        raise
