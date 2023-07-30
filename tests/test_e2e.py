import pytest

from src.domain.context_manager import ContextManager
from src.domain.events import Event
from src.domain.events import InTgText
from src.domain.events import OutTgResponse
from src.domain.events import ProxyState
from src.domain.models import Context
from src.domain.models import Proxy
from src.domain.processing import AuthProcessor
from src.domain.processing import ContextExistProcessor
from src.domain.processing import ContextRetrieveProcessor
from src.domain.processing import ContextSaveProcessor
from src.domain.processing import OutContextExist
from src.domain.processing import OutGPTResultRouter
from src.domain.processing import PredictProcessor
from src.domain.processing import ProxyRouter
from src.domain.processing import TgInProcessor
from src.services.message_bus import ConcreteMessageBus
from src.services.unit_of_work import InMemoryUnitOfWork


class FakeOutTg:
    def __init__(self) -> None:
        self.messages: list[OutTgResponse] = []

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, OutTgResponse):
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
    uow = InMemoryUnitOfWork()

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

    context_manager = ContextManager(bus=bus, uow=uow)

    for p in processors:
        bus.register(p(context_manager=context_manager))
    bus.register(fot)

    proxy_to_add = ProxyState(proxy=FakeProxy(url=""), ready=True)
    test_message = InTgText(chat_id="123", text="привет")

    await bus.public_message(proxy_to_add)
    await bus.public_message(test_message)

    assert len(fot.messages) == 1

    test_message2 = InTgText(chat_id="123", text="что делаешь?")
    await bus.public_message(test_message2)

    assert "Telegram_123" in uow.repo.context
    assert len(uow.repo.context["Telegram_123"].messages) == 4
