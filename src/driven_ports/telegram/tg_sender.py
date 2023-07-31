import asyncio
from abc import ABC
from abc import abstractmethod

import aiogram

from src.domain.events import OutTgResponse
from src.domain.events import TgEditText
from src.settings import logger


class MessageSender(ABC):
    @abstractmethod
    async def send(self, message: OutTgResponse) -> str:
        raise NotImplementedError

    @abstractmethod
    async def edit_text(self, message: TgEditText) -> None:
        raise NotImplementedError


class TgSender(MessageSender):
    def __init__(self, bot: aiogram.Bot) -> None:
        """Initialize of sender"""
        self.bot = bot

    async def send(self, message: OutTgResponse) -> str:
        """Send to outer service"""
        logger.info("send message")
        reply_markup = None
        if message.inline_buttons:
            buttons = [
                [
                    aiogram.types.InlineKeyboardButton(
                        text=y.text, callback_data=y.callback_data
                    )
                    for y in x
                ]
                for x in message.inline_buttons.buttons
            ]
            reply_markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=buttons)
        sent_message = await self.bot.send_message(
            chat_id=message.identity.channel_id,
            text=message.text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        await asyncio.sleep(0.5)
        return str(sent_message.message_id)

    async def edit_text(self, message: TgEditText) -> None:
        logger.info("edit message")
        reply_markup = None
        if message.inline_buttons:
            buttons = [
                [
                    aiogram.types.InlineKeyboardButton(
                        text=y.text, callback_data=y.callback_data
                    )
                    for y in x
                ]
                for x in message.inline_buttons.buttons
            ]
            reply_markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await self.bot.edit_message_text(
            chat_id=message.identity.channel_id,
            message_id=message.message_id,
            text=message.text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
