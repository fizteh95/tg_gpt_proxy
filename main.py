import asyncio
import typing as tp

from aiogram import Bot

from src import settings
from src.domain.events import ProxyState
from src.domain.processing import (
    AuthProcessor,
    ContextExistProcessor,
    ContextRetrieveProcessor,
    ContextSaveProcessor,
    OutContextExist,
    OutGPTResultRouter,
    OutTgResponse,
    PredictProcessor,
    ProxyChecker,
    ProxyRouter,
    TgInProcessor,
)
from src.driven_ports.telegram.tg_sender import TgSender
from src.driven_ports.telegram.wrapper import SenderWrapper
from src.leading_ports.telegram.adapter import TgListenerAdapter
from src.leading_ports.telegram.tg_poller import TgPoller
from src.services.message_bus import ConcreteMessageBus


async def bootstrap() -> tp.Any:
    to_gather: list[tp.Coroutine[None, None, None]] = []

    bus = ConcreteMessageBus()
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

    proxy_checker = ProxyChecker(bus=bus)

    for p in processors:
        bus.register(p())

    proxy_to_add = ProxyState(proxy_checker.proxies[0], ready=True)

    await bus.public_message(proxy_to_add)

    # Telegram
    bot = Bot(token=settings.TG_BOT_TOKEN)

    tg_adapter = TgListenerAdapter(uow=None, bus=bus)
    tg_poller = TgPoller(bot=bot, message_handler=tg_adapter.message_handler)
    to_gather.append(tg_poller.listen())

    tg_sender = TgSender(bot=bot)
    wrapped_sender = SenderWrapper(sender=tg_sender)
    bus.register(wrapped_sender)

    return asyncio.gather(*to_gather)


async def main() -> None:
    init_app = await bootstrap()
    await init_app


asyncio.run(main())
