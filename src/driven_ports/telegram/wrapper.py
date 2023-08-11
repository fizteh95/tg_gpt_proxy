from abc import ABC
from abc import abstractmethod

from src.domain.events import Event
from src.domain.events import MessageToDelete
from src.domain.events import OutTgResponse
from src.domain.events import TgBotTyping
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
            if (
                message.to_save_like
                or message.not_pushed_to_delete
                or message.not_pushed_to_edit_text
            ):
                async with self.uow as u:
                    await u.repo.save_out_tg_message(
                        chat_id=message.identity.channel_id,
                        text=message.text,
                        text_like=message.to_save_like,
                        message_id=message_id,
                        not_pushed_to_delete=message.not_pushed_to_delete,
                        not_pushed_to_edit_text=message.not_pushed_to_edit_text,
                    )
        elif isinstance(message, TgEditText):
            async with self.uow as u:
                (
                    _,
                    message_id,
                    not_pushed_to_edit_text,
                ) = await u.repo.get_saved_tg_message(
                    chat_id=message.identity.channel_id, text_like=message.to_edit_like
                )
                if not_pushed_to_edit_text:
                    await u.repo.remove_out_tg_message(
                        chat_id=message.identity.channel_id, message_id=message_id
                    )
            message.message_id = message_id
            await self.sender.edit_text(message=message)
        elif isinstance(message, MessageToDelete):
            # await self.sender.delete_message(message=message)
            pass
        elif isinstance(message, TgBotTyping):
            await self.sender.send_typing(chat_id=message.chat_id)
        return []
