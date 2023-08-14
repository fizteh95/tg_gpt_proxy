import asyncio
import typing as tp

from aiogram import Bot

from src import settings
from src.domain.access_manager import AccessManager
from src.domain.context_manager import ContextManager
from src.domain.processing import AccessRefreshProcessor
from src.domain.processing import AuthProcessor
from src.domain.processing import ContextExistProcessor
from src.domain.processing import ContextRetrieveProcessor
from src.domain.processing import ContextSaveProcessor
from src.domain.processing import OutContextExist
from src.domain.processing import OutGPTResultRouter
from src.domain.processing import PredictProcessor
from src.domain.processing import ProxyChecker
from src.domain.processing import ProxyRouter
from src.domain.processing import ResolutionDeclineRouter
from src.domain.processing import Spy
from src.domain.processing import TgInProcessor
from src.domain.proxy_manager import ProxyManager
from src.domain.user_state_manager import UserStateManager
from src.driven_ports.telegram.tg_sender import TgSender
from src.driven_ports.telegram.wrapper import TgSenderWrapper
from src.leading_ports.telegram.adapter import MessagePollerAdapter
from src.leading_ports.telegram.tg_poller import TgPoller
from src.services.message_bus import ConcreteMessageBus
from src.services.unit_of_work import InMemoryUnitOfWork  # noqa
from src.services.unit_of_work import SQLAlchemyUnitOfWork  # noqa

settings.logging.config.dictConfig(settings.LOGGING)  # noqa


async def bootstrap() -> tp.Any:
    to_gather: list[tp.Coroutine[None, None, None]] = []
    # await asyncio.sleep(10)

    uow = SQLAlchemyUnitOfWork()
    async with uow as u:
        await u.repo.prepare_db()
    bus = ConcreteMessageBus()

    settings.logging.config.dictConfig(settings.LOGGING)  # noqa

    context_manager = ContextManager(bus=bus, uow=uow)
    user_state_manager = UserStateManager(bus=bus, uow=uow)
    access_manager = AccessManager(bus=bus, uow=uow)
    proxy_manager = ProxyManager(bus=bus, uow=uow)

    processors = [
        TgInProcessor,
        AuthProcessor,
        ContextExistProcessor,
        ContextRetrieveProcessor,
        ProxyRouter,
        PredictProcessor,
        AccessRefreshProcessor,
        OutContextExist,
        ContextSaveProcessor,
        OutGPTResultRouter,
        ResolutionDeclineRouter,
        ProxyChecker,
        Spy,
    ]
    created_processors = []

    for p in processors:
        processor = p(
            context_manager=context_manager,
            user_state_manager=user_state_manager,
            access_manager=access_manager,
            proxy_manager=proxy_manager,
        )
        bus.register(processor)
        created_processors.append(processor)

    for cp in created_processors:
        if hasattr(cp, "start"):
            asyncio.create_task(cp.start())

    # Telegram
    bot = Bot(token=settings.TG_BOT_TOKEN)

    tg_adapter = MessagePollerAdapter(uow=uow, bus=bus)
    tg_poller = TgPoller(bot=bot, message_handler=tg_adapter.message_handler)
    to_gather.append(tg_poller.listen())

    tg_sender = TgSender(bot=bot)
    wrapped_sender = TgSenderWrapper(sender=tg_sender, uow=uow, bus=bus)
    bus.register(wrapped_sender)

    return asyncio.gather(*to_gather)


async def main() -> None:
    init_app = await bootstrap()
    await init_app


asyncio.run(main())
