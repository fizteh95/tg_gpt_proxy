from src.domain.models import Context
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class ContextManager:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus

    async def get_context(self, user_id: str) -> Context:
        async with self.uow as uow:
            context = await uow.repo.get_context(user_id=user_id)
        if context is None:
            context = Context(messages=[])
        return context

    async def add_event_in_context(
        self, user_id: str, event: dict[str, str]
    ) -> Context:
        context = await self.get_context(user_id=user_id)
        context.messages.append(event)
        async with self.uow as uow:
            await uow.repo.save_context(user_id=user_id, context=context)
        return context

    async def clear_context(self, user_id: str) -> None:
        async with self.uow as uow:
            await uow.repo.clear_context(user_id=user_id)

    async def pop_last_user_question(self, user_id: str) -> None:
        context = await self.get_context(user_id=user_id)
        new_context = Context(messages=context.messages[:-1])
        async with self.uow as uow:
            await uow.repo.save_context(user_id=user_id, context=new_context)

    async def is_user_has_last_answer(self, user_id: str) -> bool:
        context = await self.get_context(user_id=user_id)
        try:
            if context.messages[-1]["role"] == "assistant":
                return True
        except (
            KeyError,
            IndexError,
        ):
            return True
        return False
