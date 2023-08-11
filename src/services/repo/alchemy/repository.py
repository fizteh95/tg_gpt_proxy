import typing as tp

import sqlalchemy as sa  # noqa
from alembic import command
from alembic import config
from sqlalchemy.exc import IntegrityError  # noqa
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select

from src import settings
from src.domain.models import AccessCounter
from src.domain.models import Context
from src.domain.models import TgUser
from src.services.repo import AbstractRepo
from src.services.repo.alchemy.models import access_counter as access_counter_table
from src.services.repo.alchemy.models import out_tg_message
from src.services.repo.alchemy.models import sa_metadata
from src.services.repo.alchemy.models import tg_user as tg_user_table
from src.services.repo.alchemy.models import tg_user_state
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
        return Context(messages=saved_context.context)

    async def clear_context(self, user_id: str) -> None:
        await self.session.execute(
            sa.update(user_context)
            .where(user_context.c.user_id == user_id)
            .values(
                context=[],
            )
        )

    async def create_tg_user(self, tg_user: TgUser) -> None:
        await self.session.execute(
            tg_user_table.insert(),
            [
                dict(
                    chat_id=tg_user.chat_id,
                    username=tg_user.username,
                    name=tg_user.name,
                    surname=tg_user.surname,
                )
            ],
        )

    async def get_tg_user(self, chat_id: str) -> TgUser | None:
        result = await self.session.execute(
            select(tg_user_table).where(tg_user_table.c.chat_id == chat_id)
        )
        tg_user = result.first()
        if tg_user is None:
            return None
        saved_user = TgUser(
            chat_id=tg_user.chat_id,
            username=tg_user.username,
            name=tg_user.name,
            surname=tg_user.surname,
        )
        return saved_user

    async def change_tg_user_state(
        self, chat_id: str, state_map: str, state: str
    ) -> None:
        updated = await self.session.execute(
            sa.update(tg_user_state)
            .where(
                tg_user_state.c.chat_id == chat_id,
                tg_user_state.c.state_map == state_map,
            )
            .values(
                state=state,
            )
        )
        if updated.rowcount == 0:
            await self.session.execute(
                tg_user_state.insert(),
                [
                    dict(
                        chat_id=chat_id,
                        state_map=state_map,
                        state=state,
                    )
                ],
            )

    async def get_tg_user_state(self, chat_id: str) -> dict[str, str]:
        result = await self.session.execute(
            select(tg_user_state).where(tg_user_state.c.chat_id == chat_id)
        )
        user_states: dict[str, str] = {}
        for row in result.fetchall():
            user_states[row.state_map] = row.state
        return user_states

    async def get_access_counter(self, user_id: str) -> AccessCounter | None:
        result = await self.session.execute(
            select(access_counter_table).where(
                access_counter_table.c.user_id == user_id
            )
        )
        acc_counter = result.first()
        if acc_counter is None:
            return None
        saved_acc_counter = AccessCounter(
            remain_per_day=acc_counter.remain_per_day,
            remain_per_all_time=acc_counter.remain_per_all_time,
        )
        return saved_acc_counter

    async def set_access_counter_usual_for_everybody(self, count_level: int) -> None:
        await self.session.execute(
            sa.update(access_counter_table).values(
                remain_per_day=count_level,
            )
        )

    async def set_access_counter(
        self, user_id: str, access_counter: AccessCounter
    ) -> None:
        updated = await self.session.execute(
            sa.update(access_counter_table)
            .where(access_counter_table.c.user_id == user_id)
            .values(
                remain_per_day=access_counter.remain_per_day,
                remain_per_all_time=access_counter.remain_per_all_time,
            )
        )
        if updated.rowcount == 0:
            await self.session.execute(
                access_counter_table.insert(),
                [
                    dict(
                        user_id=user_id,
                        remain_per_day=access_counter.remain_per_day,
                        remain_per_all_time=access_counter.remain_per_all_time,
                    )
                ],
            )

    async def save_out_tg_message(
        self,
        chat_id: str,
        text: str,
        text_like: str,
        message_id: str,
        not_pushed_to_delete: bool,
        not_pushed_to_edit_text: str = "",
        pushed: bool = False,
    ) -> None:
        await self.session.execute(
            out_tg_message.insert(),
            [
                dict(
                    chat_id=chat_id,
                    text=text,
                    text_like=text_like,
                    message_id=message_id,
                    not_pushed_to_delete=not_pushed_to_delete,
                    not_pushed_to_edit_text=not_pushed_to_edit_text,
                    pushed=pushed,
                )
            ],
        )

    async def make_saved_message_pushed(
        self, chat_id: str, message_text_like: str
    ) -> None:
        await self.session.execute(
            sa.update(out_tg_message)
            .where(
                out_tg_message.c.chat_id == chat_id,
                out_tg_message.c.text_like == message_text_like,
            )
            .values(pushed=True)
        )

    async def get_exist_not_pushed_message_to_delete(self, chat_id: str) -> str | None:
        result = await self.session.execute(
            select(out_tg_message)
            .where(
                out_tg_message.c.chat_id == chat_id,
                out_tg_message.c.pushed != True,  # noqa
                out_tg_message.c.not_pushed_to_delete == True,  # noqa
            )
            .order_by(out_tg_message.c.id.desc())
        )
        not_pushed_message = result.first()
        if not_pushed_message is None:
            return None
        not_pushed_message_id: str = not_pushed_message.message_id
        return not_pushed_message_id

    async def get_exist_not_pushed_message_to_edit(
        self, chat_id: str
    ) -> tuple[str, str, str] | tuple[None, None, None]:
        result = await self.session.execute(
            select(out_tg_message)
            .where(
                out_tg_message.c.chat_id == chat_id,
                out_tg_message.c.pushed != True,  # noqa
                out_tg_message.c.not_pushed_to_edit_text != "",
            )
            .order_by(out_tg_message.c.id.desc())
        )
        not_pushed_message = result.first()
        if not_pushed_message is None:
            return None, None, None
        message_id: str = not_pushed_message.message_id
        to_edit_text: str = not_pushed_message.not_pushed_to_edit_text
        text_like: str = not_pushed_message.text_like
        return message_id, to_edit_text, text_like

    async def remove_out_tg_message(self, chat_id: str, message_id: str) -> None:
        await self.session.execute(
            out_tg_message.delete().where(
                out_tg_message.c.chat_id == chat_id,
                out_tg_message.c.message_id == message_id,
            )
        )

    async def get_saved_tg_message(
        self, chat_id: str, text_like: str
    ) -> tuple[str, str, str]:
        result = await self.session.execute(
            select(out_tg_message)
            .where(
                out_tg_message.c.chat_id == chat_id,
                out_tg_message.c.text_like == text_like,
            )
            .order_by(out_tg_message.c.id.desc())
        )
        saved_message = result.first()
        text: str = saved_message.text
        message_id: str = saved_message.message_id
        not_pushed_to_edit_text: str = saved_message.not_pushed_to_edit_text
        return text, message_id, not_pushed_to_edit_text
