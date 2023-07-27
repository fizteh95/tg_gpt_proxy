from src.domain.events import InTgCommand
from src.domain.events import InTgText


class TgListenerAdapter:
    def __init__(self, uow, bus) -> None:
        self.uow = uow
        self.bus = bus

    async def message_handler(self, message: InTgText | InTgCommand) -> None:
        # async with self.uow as u:
        #     await u.repo.save_command(message)
        await self.bus.public_message(message=message)
        return None
