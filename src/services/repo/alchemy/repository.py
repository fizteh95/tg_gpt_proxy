import typing as tp

import sqlalchemy as sa  # noqa
from alembic import command
from alembic import config
from sqlalchemy.exc import IntegrityError  # noqa
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select

from src import settings
from src.domain.models import Context
from src.services.repo import AbstractRepo
from src.services.repo.alchemy.models import sa_metadata
from src.services.repo.alchemy.models import user_context


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
        print(f"tp4 {context}")
        try:
            await self.session.execute(
                user_context.insert(),
                [
                    dict(
                        user_id=user_id,
                        context=context.messages,
                    )
                ],
            )
        except IntegrityError:
            await self.session.rollback()
            await self.session.execute(
                sa.update(user_context)
                .where(user_context.c.user_id == user_id)
                .values(
                    context=context.messages,
                )
            )

    async def get_context(self, user_id: str) -> Context | None:
        result = await self.session.execute(
            select(user_context).where(user_context.c.user_id == user_id)
        )
        saved_context = result.first()
        if saved_context is None:
            return None
        print(f"tp0 {saved_context}")
        return Context(messages=saved_context.context)

    async def clear_context(self, user_id: str) -> None:
        await self.session.execute(
            sa.update(user_context)
            .where(user_context.c.user_id == user_id)
            .values(
                context=[],
            )
        )
