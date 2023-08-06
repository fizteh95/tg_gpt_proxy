import typing as tp
from abc import ABC
from abc import abstractmethod

import aiogram

from src.domain.events import InTgButtonPushed
from src.domain.events import InTgCommand
from src.domain.events import InTgText
from src.domain.models import TgUser
from src.settings import logger


class MessagePoller(ABC):
    def __init__(
        self,
        message_handler: tp.Callable[
            [InTgText | InTgCommand | InTgButtonPushed], tp.Awaitable[None]
        ],  # TODO: поменять классы на базовые
        *args: tp.Any,
        **kwargs: tp.Any,
    ) -> None:
        self.message_handler = message_handler

    @abstractmethod
    async def listen(self) -> None:
        raise NotImplementedError


class TgPoller(MessagePoller):
    def __init__(
        self,
        message_handler: tp.Callable[
            [InTgText | InTgCommand | InTgButtonPushed], tp.Awaitable[None]
        ],
        bot: aiogram.Bot,
    ) -> None:
        """Initialize of entrypoints"""
        super().__init__(bot=bot, message_handler=message_handler)
        self.bot = bot
        self.dp = aiogram.Dispatcher(self.bot)
        self.dp.register_message_handler(self.process_message)
        self.dp.register_callback_query_handler(self.process_push_inline_button)

    async def process_push_inline_button(
        self, query: aiogram.types.CallbackQuery
    ) -> None:
        tg_user = TgUser(
            chat_id=str(query.from_user.id),
            name=query.from_user.first_name,
            surname=query.from_user.last_name,
            username=query.from_user.username,
        )
        event = InTgButtonPushed(tg_user=tg_user, data=query.data)
        await self.message_handler(event)

    async def process_message(self, tg_message: aiogram.types.Message) -> None:
        """Process message from telegram"""
        logger.info(f"new text from entrypoints {tg_message.text}")
        try:
            text = tg_message.text
        except Exception as e:
            raise e

        tg_user = TgUser(
            chat_id=str(tg_message.chat.id),
            name=tg_message.from_user.first_name,
            surname=tg_message.from_user.last_name,
            username=tg_message.from_user.username,
        )
        if text[0] == "/":
            event = InTgCommand(
                tg_user=tg_user,
                command=text[1:],
            )
        else:
            event = InTgText(  # type: ignore
                tg_user=tg_user,
                text=text,
            )
        await self.message_handler(event)

    async def listen(self) -> None:
        """Poll from outer service. Must be run in background task"""
        logger.info("Start polling")
        try:
            try:
                await self.dp.start_polling()
            except Exception as e:
                raise e
        finally:
            await self.bot.close()
