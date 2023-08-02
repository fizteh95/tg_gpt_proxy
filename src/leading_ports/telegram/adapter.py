from src.domain.events import InTgButtonPushed
from src.domain.events import InTgCommand
from src.domain.events import InTgText
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class MessagePollerAdapter:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus

    async def message_handler(
        self, message: InTgText | InTgCommand | InTgButtonPushed
    ) -> None:
        async with self.uow as u:
            user = await u.repo.get_tg_user(chat_id=message.tg_user.chat_id)
            if not user:
                await u.repo.create_tg_user(tg_user=message.tg_user)

        await self.bus.public_message(message=message)
        return None
