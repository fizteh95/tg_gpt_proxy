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
from src.domain.user_state_manager import UserStateManager
from src.driven_ports.telegram.tg_sender import TgSender
from src.driven_ports.telegram.wrapper import TgSenderWrapper
from src.leading_ports.telegram.adapter import MessagePollerAdapter
from src.leading_ports.telegram.tg_poller import TgPoller
from src.services.message_bus import ConcreteMessageBus
from src.services.unit_of_work import InMemoryUnitOfWork  # noqa
from src.services.unit_of_work import SQLAlchemyUnitOfWork  # noqa


async def bootstrap() -> tp.Any:
    to_gather: list[tp.Coroutine[None, None, None]] = []

    uow = InMemoryUnitOfWork()
    async with uow as u:
        await u.repo.prepare_db()
    bus = ConcreteMessageBus()

    context_manager = ContextManager(bus=bus, uow=uow)
    user_state_manager = UserStateManager(bus=bus, uow=uow)
    access_manager = AccessManager(bus=bus, uow=uow)

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
        ResolutionDeclineRouter,
        Spy,
    ]

    proxy_checker = ProxyChecker(bus=bus)
    access_refresh_processor = AccessRefreshProcessor(
        context_manager=context_manager,
        user_state_manager=user_state_manager,
        access_manager=access_manager,
    )

    for p in processors:
        bus.register(
            p(
                context_manager=context_manager,
                user_state_manager=user_state_manager,
                access_manager=access_manager,
            )
        )

    # proxy_to_add = ProxyState(proxy_checker.proxies[0], ready=True)
    #
    # await bus.public_message(proxy_to_add)
    asyncio.create_task(proxy_checker.start())
    asyncio.create_task(access_refresh_processor.start())

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
