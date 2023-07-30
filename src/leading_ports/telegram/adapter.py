from src.domain.events import InTgCommand
from src.domain.events import InTgText
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class MessagePollerAdapter:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus

    async def message_handler(self, message: InTgText | InTgCommand) -> None:
        # async with self.uow as u:
        #     await u.repo.save_command(message)
        await self.bus.public_message(message=message)
        return None
