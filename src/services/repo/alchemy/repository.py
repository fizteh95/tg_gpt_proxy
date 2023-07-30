import typing as tp

import sqlalchemy as sa  # noqa
from alembic import command
from alembic import config
from sqlalchemy.exc import IntegrityError  # noqa
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine

from src import settings
from src.domain.models import Context
from src.services.repo import AbstractRepo
from src.services.repo.alchemy.models import sa_metadata

# from sqlalchemy.future import select
# from src.services.repo.alchemy.models import in_command


class SQLAlchemyRepo(AbstractRepo):
    def __init__(self, session: tp.Any) -> None:
        self.session = session

    async def prepare_db(self) -> None:
        await self.run_async_upgrade()

    @staticmethod
    def run_upgrade(connection, cfg) -> None:  # type: ignore
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    async def run_async_upgrade(self) -> None:
        engine = create_async_engine(settings.ENGINE_STRING)  # , echo=True
        async with engine.begin() as conn:
            await conn.run_sync(self.run_upgrade, config.Config("alembic.ini"))

    @staticmethod
    async def _recreate_db(engine: AsyncEngine) -> None:
        """
        ONLY FOR IN_MEMORY SQLITE DB!!!
        :return:
        """
        async with engine.begin() as conn:
            await conn.run_sync(sa_metadata.drop_all)
        async with engine.begin() as conn:
            await conn.run_sync(sa_metadata.create_all)

    async def save_context(self, user_id: str, context: Context) -> None:
        raise NotImplementedError

    async def get_context(self, user_id: str) -> Context | None:
        raise NotImplementedError

    async def clear_context(self, user_id: str) -> None:
        raise NotImplementedError
