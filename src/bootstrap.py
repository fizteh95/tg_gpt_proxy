import asyncio
import typing as tp

from src.services.message_bus import MessageBus

# from src.service_layer.unit_of_work import AbstractUnitOfWork


async def bootstrap(
    # uow: tp.Type[AbstractUnitOfWork],
    bus: tp.Type[MessageBus],
) -> tp.Any:
    # concrete_uow = uow()
    # async with concrete_uow as u:
    #     await u.repo.prepare_db()
    # concrete_bus = bus()

    ...

    to_gather: list[tp.Coroutine[None, None, None]] = []

    ...

    return asyncio.gather(*to_gather)
