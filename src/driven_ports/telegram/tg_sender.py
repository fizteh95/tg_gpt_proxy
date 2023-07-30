import asyncio
from abc import ABC
from abc import abstractmethod

import aiogram

from src.domain.events import OutResponse
from src.settings import logger


class MessageSender(ABC):
    @abstractmethod
    async def send(self, message: OutResponse) -> None:
        raise NotImplementedError


class TgSender(MessageSender):
    def __init__(self, bot: aiogram.Bot) -> None:
        """Initialize of sender"""
        self.bot = bot

    async def send(self, message: OutResponse) -> None:
        """Send to outer service"""
        logger.info("send message")
        _ = await self.bot.send_message(
            chat_id=message.identity.channel_id,
            text=message.text,
            reply_markup=None,
            parse_mode="Markdown",
        )
        await asyncio.sleep(0.5)
