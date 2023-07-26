import typing as tp

from src.domain.events import Event


class Subscriber(tp.Protocol):
    async def handle_message(self, message: Event) -> list[Event]:
        """Handle message from bus"""
