import asyncio

import aiogram

from src.domain.events import OutTgText, OutTgResponse
from src.settings import logger


class TgSender:
    def __init__(self, bot: aiogram.Bot) -> None:
        """Initialize of sender"""
        super().__init__()
        self.bot = bot

    async def send(self, message: OutTgResponse) -> None:
        """Send to outer service"""
        logger.info("send message")
        _ = await self.bot.send_message(
            chat_id=message.identity.channel_id,
            text=message.text,
            reply_markup=None,
            parse_mode="Markdown",
        )
        await asyncio.sleep(0.5)
