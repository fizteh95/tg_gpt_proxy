import pytest

from src.domain.access_manager import AccessManager
from src.domain.context_manager import ContextManager
from src.domain.events import Event
from src.domain.events import InTgText
from src.domain.events import OutTgResponse
from src.domain.events import ProxyState
from src.domain.models import Context
from src.domain.models import Proxy
from src.domain.models import TgUser
from src.domain.processing import AuthProcessor
from src.domain.processing import ContextExistProcessor
from src.domain.processing import ContextRetrieveProcessor
from src.domain.processing import ContextSaveProcessor
from src.domain.processing import OutContextExist
from src.domain.processing import OutGPTResultRouter
from src.domain.processing import PredictProcessor
from src.domain.processing import ProxyRouter
from src.domain.processing import TgInProcessor
from src.domain.proxy_manager import ProxyManager
from src.domain.user_state_manager import UserStateManager
from src.services.message_bus import ConcreteMessageBus
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork
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


class FakeProxyManager(ProxyManager):
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:  # noqa
        self.uow = uow
        self.bus = bus
        self.proxies = {"fake_proxy": FakeProxy()}
        self.proxy_status = {"fake_proxy": True}


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
    user_state_manager = UserStateManager(bus=bus, uow=uow)
    access_manager = AccessManager(bus=bus, uow=uow)
    proxy_manager = FakeProxyManager(bus=bus, uow=uow)

    for p in processors:
        bus.register(
            p(
                context_manager=context_manager,
                user_state_manager=user_state_manager,
                access_manager=access_manager,
                proxy_manager=proxy_manager,
            )
        )
    bus.register(fot)

    proxy_to_add = ProxyState(proxy=FakeProxy(), ready=True)
    tg_user = TgUser(chat_id="123")
    test_message = InTgText(tg_user=tg_user, text="привет")

    await bus.public_message(proxy_to_add)
    await bus.public_message(test_message)

    assert len(fot.messages) == 2

    test_message2 = InTgText(tg_user=tg_user, text="что делаешь?")
    await bus.public_message(test_message2)

    assert "Telegram_123" in uow.repo.context
    assert len(uow.repo.context["Telegram_123"].messages) == 4
