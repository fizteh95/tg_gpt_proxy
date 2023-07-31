from src.domain.models import Context
from src.domain.models import StateMap
from src.domain.models import TgState
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class UserStateManager:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus

    async def get_user_proxy_name(self, chat_id: str) -> str:
        async with self.uow as uow:
            user_states = await uow.repo.get_tg_user_state(chat_id=chat_id)
        proxy_name = user_states.get(StateMap.current_proxy.value, "")
        return proxy_name

    async def set_user_proxy_name(self, chat_id: str, proxy_name: str) -> None:
        async with self.uow as uow:
            await uow.repo.change_tg_user_state(
                chat_id=chat_id,
                state_map=StateMap.current_proxy.value,
                state=proxy_name,
            )

    async def set_user_tg_state(self, chat_id: str, state: TgState) -> None:
        async with self.uow as uow:
            await uow.repo.change_tg_user_state(
                chat_id=chat_id,
                state_map=StateMap.tg_state.value,
                state=state.value,
            )
