from src.domain.events import Event, OutTgText, OutTgResponse


class SenderWrapper:
    def __init__(self, sender) -> None:
        self.sender = sender

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, OutTgResponse):
            await self.sender.send(message=message)
        return []
