import pytest

from src.domain.events import Event, OutTgText, ProxyState, TgText
from src.domain.models import Context, Proxy
from src.domain.processing import (
    AuthProcessor,
    ContextExistProcessor,
    ContextRetrieveProcessor,
    ContextSaveProcessor,
    OutContextExist,
    OutGPTResultRouter,
    PredictProcessor,
    ProxyRouter,
    TgInProcessor,
)
from src.services.message_bus import ConcreteMessageBus


class FakeOutTg:
    def __init__(self):
        self.messages = []

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, OutTgText):
            self.messages.append(message)
            print(f"GPT > {message.text}")
        return []


class FakeProxy(Proxy):
    async def generate(self, content: Context) -> str:
        return "Привет!"


@pytest.mark.asyncio
async def test_everything() -> None:
    bus = ConcreteMessageBus()
    fot = FakeOutTg()

    processors = [
        TgInProcessor,
        AuthProcessor,
        ContextExistProcessor,
        ContextRetrieveProcessor,
        ProxyRouter,
        PredictProcessor,
        OutContextExist,
        ContextSaveProcessor,
        OutGPTResultRouter,
    ]

    for p in processors:
        bus.register(p())
    bus.register(fot)

    proxy_to_add = ProxyState(proxy=FakeProxy(url=""), ready=True)
    test_message = TgText(chat_id="123", text="привет")

    await bus.public_message(proxy_to_add)
    await bus.public_message(test_message)

    assert len(fot.messages) == 1
