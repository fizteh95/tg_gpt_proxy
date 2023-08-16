import asyncio
from abc import ABC
from abc import abstractmethod

import aiogram

from src.domain.events import OutTgResponse
from src.domain.events import TgEditText
from src.domain.models import TgInlineButtonArray
from src.settings import logger


class MessageSender(ABC):
    @abstractmethod
    async def send(self, message: OutTgResponse) -> str:
        raise NotImplementedError

    @abstractmethod
    async def edit_text(self, message: TgEditText) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_typing(self, chat_id: str) -> None:
        raise NotImplementedError


class TgSender(MessageSender):
    def __init__(self, bot: aiogram.Bot) -> None:
        """Initialize of sender"""
        self.bot = bot
        self.text_length_limit = 4090

    @staticmethod
    def create_reply_markup(
        inline_buttons: TgInlineButtonArray | None,
    ) -> aiogram.types.InlineKeyboardMarkup | None:
        reply_markup = None
        if inline_buttons:
            buttons = [
                [
                    aiogram.types.InlineKeyboardButton(
                        text=y.text, callback_data=y.callback_data
                    )
                    for y in x
                ]
                for x in inline_buttons.buttons
            ]
            reply_markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=buttons)
        return reply_markup

    async def send(self, message: OutTgResponse) -> str:
        """Send to outer service"""
        logger.info("send message")
        text_to_send = message.text
        if len(text_to_send) > self.text_length_limit:
            while len(text_to_send) > self.text_length_limit:
                await self.bot.send_message(
                    chat_id=message.identity.channel_id,
                    text=text_to_send[: self.text_length_limit + 1],
                    parse_mode="HTML",
                )
                text_to_send = text_to_send[self.text_length_limit + 1 :]
                await asyncio.sleep(0.5)
        reply_markup = self.create_reply_markup(message.inline_buttons)
        sent_message = await self.bot.send_message(
            chat_id=message.identity.channel_id,
            text=text_to_send,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        await asyncio.sleep(0.5)
        return str(sent_message.message_id)

    async def edit_text(self, message: TgEditText) -> None:
        logger.info("edit message")
        reply_markup = self.create_reply_markup(message.inline_buttons)
        await self.bot.edit_message_text(
            chat_id=message.identity.channel_id,
            message_id=message.message_id,
            text=message.text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    async def send_typing(self, chat_id: str) -> None:
        logger.info("send typing")
        await self.bot.send_chat_action(chat_id=chat_id, action="typing")
