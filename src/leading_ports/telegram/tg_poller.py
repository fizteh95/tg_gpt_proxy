import typing as tp

import aiogram

from src.domain.events import InTgCommand
from src.domain.events import InTgText
from src.settings import logger


class TgPoller:
    def __init__(
        self,
        message_handler: tp.Callable[[InTgText | InTgCommand], tp.Awaitable[None]],
        bot: aiogram.Bot,
    ) -> None:
        """Initialize of entrypoints"""
        self.message_handler = message_handler
        self.bot = bot
        self.dp = aiogram.Dispatcher(self.bot)
        self.dp.register_message_handler(self.process_message)

    async def process_message(self, tg_message: aiogram.types.Message) -> None:
        """Process message from telegram"""
        logger.info(f"new text from entrypoints {tg_message.text}")
        try:
            text = tg_message.text
        except Exception as e:
            raise e

        if text[0] == "/":
            event = InTgCommand(
                chat_id=tg_message.chat.id,
                command=text,
            )
        else:
            event = InTgText(  # type: ignore
                chat_id=tg_message.chat.id,
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
