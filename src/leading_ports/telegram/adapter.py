# from src.domain.events import MessageToDelete
from src.domain.events import Event
from src.domain.events import InTgButtonPushed
from src.domain.events import InTgCommand
from src.domain.events import InTgText
from src.domain.events import TgEditText
from src.domain.models import ChannelType
from src.domain.models import InputIdentity
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class MessagePollerAdapter:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus

    async def message_handler(
        self, message: InTgText | InTgCommand | InTgButtonPushed
    ) -> None:
        res: list[Event] = [message]
        async with self.uow as u:
            user = await u.repo.get_tg_user(chat_id=message.tg_user.chat_id)
            if not user:
                await u.repo.create_tg_user(tg_user=message.tg_user)
            if isinstance(message, InTgButtonPushed):
                await u.repo.make_saved_message_pushed(
                    chat_id=message.tg_user.chat_id,
                    message_text_like=f"{message.data.split()[0]}_message",
                )
            if isinstance(
                message,
                (
                    InTgText,
                    InTgCommand,
                ),
            ):
                # message_id = await u.repo.get_exist_not_pushed_message_to_delete(
                #     chat_id=message.tg_user.chat_id
                # )
                # if message_id:
                #     await u.repo.remove_out_tg_message(
                #         chat_id=message.tg_user.chat_id, message_id=message_id
                #     )
                #     res.append(
                #         MessageToDelete(
                #             chat_id=message.tg_user.chat_id, message_id=message_id
                #         )
                #     )
                pass
                (
                    message_to_edit_id,
                    to_edit_text,
                    text_like,
                ) = await u.repo.get_exist_not_pushed_message_to_edit(
                    chat_id=message.tg_user.chat_id
                )
                if message_to_edit_id and to_edit_text and text_like:
                    # await u.repo.remove_out_tg_message(
                    #     chat_id=message.tg_user.chat_id, message_id=message_to_edit_id
                    # )
                    identity = InputIdentity(
                        channel_type=ChannelType.tg, channel_id=message.tg_user.chat_id
                    )
                    res.append(
                        TgEditText(
                            identity=identity, text=to_edit_text, to_edit_like=text_like
                        )
                    )

        await self.bus.public_message(message=res)
        return None
