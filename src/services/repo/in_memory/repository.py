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
        self.out_tg_messages: list[dict[str, str | bool]] = []

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

    async def get_access_counter(self, user_id: str) -> AccessCounter | None:
        return copy.deepcopy(self.access_counter.get(user_id))

    async def set_access_counter_usual_for_everybody(self, count_level: int) -> None:
        for u in list(self.access_counter.keys()):
            self.access_counter[u].remain_per_day = count_level

    async def set_access_counter(
        self, user_id: str, access_counter: AccessCounter
    ) -> None:
        self.access_counter[user_id] = access_counter

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
        self.out_tg_messages.append(
            dict(
                chat_id=chat_id,
                text=text,
                text_like=text_like,
                message_id=message_id,
                not_pushed_to_delete=not_pushed_to_delete,
                not_pushed_to_edit_text=not_pushed_to_edit_text,
                pushed=pushed,
            )
        )

    async def make_saved_message_pushed(
        self, chat_id: str, message_text_like: str
    ) -> None:
        for m in self.out_tg_messages:
            if m["chat_id"] != chat_id or m["text_like"] != message_text_like:
                continue
            m["pushed"] = True

    async def get_exist_not_pushed_message_to_delete(self, chat_id: str) -> str | None:
        for m in self.out_tg_messages:
            if m["chat_id"] != chat_id or m["pushed"] or not m["not_pushed_to_delete"]:
                continue
            if not isinstance(m["message_id"], str):
                raise TypeError("saved message dict types incompatible")
            message_id: str = m["message_id"]
            return message_id
        return None

    async def get_exist_not_pushed_message_to_edit(
        self, chat_id: str
    ) -> tuple[str, str, str] | tuple[None, None, None]:
        for m in self.out_tg_messages:
            if (
                m["chat_id"] != chat_id
                or m["pushed"]
                or not m["not_pushed_to_edit_text"]
            ):
                continue
            if (
                not isinstance(m["message_id"], str)
                or not isinstance(m["not_pushed_to_edit_text"], str)
                or not isinstance(m["text_like"], str)
            ):
                raise TypeError("saved message dict types incompatible")
            message_id: str = m["message_id"]
            to_edit_text: str = m["not_pushed_to_edit_text"]
            text_like: str = m["text_like"]
            return message_id, to_edit_text, text_like
        return None, None, None

    async def remove_out_tg_message(self, chat_id: str, message_id: str) -> None:
        clear_messages = [
            x
            for x in self.out_tg_messages
            if x["chat_id"] != chat_id or x["message_id"] != message_id
        ]
        self.out_tg_messages = clear_messages

    async def get_saved_tg_message(
        self, chat_id: str, text_like: str
    ) -> tuple[str, str, str]:
        for item in self.out_tg_messages[::-1]:
            if item["chat_id"] == chat_id and item["text_like"] == text_like:
                if (
                    not isinstance(item["text"], str)
                    or not isinstance(item["message_id"], str)
                    or not isinstance(item["not_pushed_to_edit_text"], str)
                ):
                    raise TypeError("saved message dict types incompatible")
                message_text: str = item["text"]
                message_id: str = item["message_id"]
                not_pushed_to_edit_text: str = item["not_pushed_to_edit_text"]
                return message_text, message_id, not_pushed_to_edit_text
        raise
