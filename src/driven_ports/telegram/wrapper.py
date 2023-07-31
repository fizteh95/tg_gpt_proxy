from abc import ABC
from abc import abstractmethod

from src.domain.events import Event
from src.domain.events import OutTgResponse
from src.domain.events import TgEditText
from src.driven_ports.telegram.tg_sender import MessageSender
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class SenderWrapper(ABC):
    def __init__(
        self, sender: MessageSender, uow: AbstractUnitOfWork, bus: MessageBus
    ) -> None:
        self.sender = sender
        self.uow = uow
        self.bus = bus

    @abstractmethod
    async def handle_message(self, message: Event) -> list[Event]:
        raise NotImplementedError


class TgSenderWrapper(SenderWrapper):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, OutTgResponse):
            message_id = await self.sender.send(message=message)
            if message.to_save_like is not None:
                async with self.uow as u:
                    await u.repo.save_out_tg_message(
                        chat_id=message.identity.channel_id,
                        text=message.text,
                        text_like=message.to_save_like,
                        message_id=message_id,
                    )
        elif isinstance(message, TgEditText):
            async with self.uow as u:
                _, message_id = await u.repo.get_saved_tg_message(
                    chat_id=message.identity.channel_id, text_like=message.to_edit_like
                )
            message.message_id = message_id
            await self.sender.edit_text(message=message)
        return []
