from abc import ABC
from abc import abstractmethod

from src.domain.events import Event
from src.domain.events import OutTgResponse
from src.driven_ports.telegram.tg_sender import MessageSender


class SenderWrapper(ABC):
    def __init__(self, sender: MessageSender) -> None:
        self.sender = sender

    @abstractmethod
    async def handle_message(self, message: Event) -> list[Event]:
        raise NotImplementedError


class TgSenderWrapper(SenderWrapper):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, OutTgResponse):
            await self.sender.send(message=message)
        return []
