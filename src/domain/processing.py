import asyncio
from os import walk

from src.domain.user_state_manager import UserStateManager
from src.domain.context_manager import ContextManager
from src.domain.events import Event
from src.domain.events import GPTResult
from src.domain.events import InTgButtonPushed
from src.domain.events import InTgCommand
from src.domain.events import InTgText
from src.domain.events import OutAPIResponse
from src.domain.events import OutTgResponse
from src.domain.events import PredictOffer
from src.domain.events import PredictOfferResolutionAccept
from src.domain.events import PredictResult
from src.domain.events import PreparedProxy
from src.domain.events import ProxyState
from src.domain.events import TgEditText
from src.domain.events import ToPredict
from src.domain.events import ToRetrieveContext
from src.domain.events import ToSaveContext
from src.domain.models import ChannelType
from src.domain.models import Context
from src.domain.models import InputIdentity
from src.domain.models import Proxy
from src.domain.models import TgInlineButton
from src.domain.models import TgInlineButtonArray
from src.domain.so_loader import load_so_module
from src.domain.subscriber import Subscriber
from src.services.message_bus import MessageBus


class BaseProcessor(Subscriber):
    def __init__(
        self, context_manager: ContextManager, user_state_manager: UserStateManager
    ) -> None:
        self.context_manager = context_manager
        self.user_state_manager = user_state_manager

    async def handle_message(self, message: Event) -> list[Event]:
        raise NotImplementedError


class TgInProcessor(BaseProcessor):
    @staticmethod
    async def _get_proxy_names() -> list[dict[str, str]]:
        proxies: list[dict[str, str]] = []
        filenames = next(walk("./so/"), (None, None, []))[2]  # type: ignore
        for name in filenames:
            module = load_so_module(name)
            proxy = module.CustomProxy()
            proxies.append({"name": proxy.name, "description": proxy.description})
        return proxies

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, InTgText):
            identity = InputIdentity(
                channel_id=message.tg_user.chat_id, channel_type=ChannelType.tg
            )
            res = PredictOffer(identity=identity, text=message.text, one_hit=False)
            return [res]
        elif isinstance(message, InTgCommand):
            identity = InputIdentity(
                channel_id=message.tg_user.chat_id, channel_type=ChannelType.tg
            )
            if message.command == "start":
                greeting = (
                    "Привет! Это прокси до ChatGPT. Чтобы начать общаться, просто отправь сообщение ;)\n"
                    "Для очистки контекст отправь /clear\n"
                    "Для переключения модели отправь /set_proxy"
                )
                res_greet = OutTgResponse(identity=identity, text=greeting)
                return [res_greet]
            elif message.command == "clear":
                await self.context_manager.clear_context(user_id=identity.to_str)
                clear_response = "Контекст очищен."
                res_clear = OutTgResponse(identity=identity, text=clear_response)
                return [res_clear]
            elif message.command == "set_proxy":
                proxy_list = await self._get_proxy_names()
                buttons: list[list[TgInlineButton]] = []
                res_text = "<b>Выберите прокси для общения:</b>\n\n"
                for e, p in enumerate(proxy_list):
                    res_text += f"{e + 1}. {p['name']} - {p['description']}\n"
                    buttons.append(
                        [
                            TgInlineButton(
                                text=f"{e + 1}. {p['name']}",
                                callback_data=f"proxy_choice {p['name']}",
                            )
                        ]
                    )
                res_text = res_text[:-1]
                res_proxy_choice = OutTgResponse(
                    identity=identity,
                    text=res_text,
                    inline_buttons=TgInlineButtonArray(buttons=buttons),
                    to_save_like="proxy_choice_message",
                )
                return [res_proxy_choice]
        elif isinstance(message, InTgButtonPushed):
            identity = InputIdentity(
                channel_id=message.tg_user.chat_id, channel_type=ChannelType.tg
            )
            if message.data.split()[0] == "proxy_choice":
                proxy_name = message.data[len(message.data.split()[0]) + 1 :]
                await self.user_state_manager.set_user_proxy_name(
                    chat_id=message.tg_user.chat_id, proxy_name=proxy_name
                )
                edit_text = f"Выбран прокси: {proxy_name}"
                edit_res = TgEditText(
                    identity=identity,
                    text=edit_text,
                    to_edit_like="proxy_choice_message",
                )
                return [edit_res]
        return []


class AuthProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PredictOffer):
            res = PredictOfferResolutionAccept(offer=message)
            return [res]
        return []


class ContextExistProcessor(BaseProcessor):
    """
    Класс для проверки, нужно ли вытаскивать контекст из БД
    """

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PredictOfferResolutionAccept):
            if (
                message.offer.context
                and not message.offer.text
                and not message.offer.one_hit
            ):
                res = ToPredict(offer=message.offer, context=message.offer.context)
                return [res]
            elif (
                message.offer.text
                and not message.offer.context
                and message.offer.one_hit
            ):
                context = Context(
                    messages=[{"role": "user", "content": message.offer.text}]
                )
                res = ToPredict(offer=message.offer, context=context)
                return [res]
            elif message.offer.text and not message.offer.one_hit:
                res_retrieve = ToRetrieveContext(offer=message.offer)
                return [res_retrieve]
            else:
                raise
        return []


class ContextRetrieveProcessor(BaseProcessor):
    """
    Класс для вытаскивания имеющегося контекста и сохранения входящего сообщения в него
    """

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, ToRetrieveContext):
            if message.offer.text is None:
                raise
            event_to_add = {"role": "user", "content": message.offer.text}
            context = await self.context_manager.add_event_in_context(
                user_id=message.offer.identity.to_str, event=event_to_add
            )
            print(f"tp3 {context}")
            res = ToPredict(offer=message.offer, context=context)
            return [res]
        return []


class ProxyChecker:
    """
    Загружает классы прокси из папки и периодически пингует их сообщениями
    """

    def __init__(self, bus: MessageBus) -> None:
        self.bus = bus
        self.proxies: list[Proxy] = []
        # loading proxies
        filenames = next(walk("./so/"), (None, None, []))[2]  # type: ignore
        for name in filenames:
            module = load_so_module(name)
            proxy = module.CustomProxy()
            self.proxies.append(proxy)

    async def start(self) -> None:
        # TODO: сделать по красоте
        while True:
            working_proxies = []
            not_working_proxies = []
            test_context = Context(
                messages=[{"role": "user", "content": "Привет, как дела?"}]
            )
            # проверка
            for p in self.proxies:
                try:
                    res = await p.generate(content=test_context)
                    if isinstance(res, str) and len(res) > 0:
                        print(f"proxy working, {p}")
                        working_proxies.append(p)
                except Exception as e:
                    print(f"Proxy checker error: proxy={p.name}, error={e}")
                    not_working_proxies.append(p)
            # отправка результатов
            res_list: list[Event] = []
            for w in working_proxies:
                t1 = ProxyState(proxy=w, ready=True)
                res_list.append(t1)
            for nw in not_working_proxies:
                t2 = ProxyState(proxy=nw, ready=False)
                res_list.append(t2)
            print(f"proxy list: {res_list}")
            await self.bus.public_message(message=res_list)
            # спим
            await asyncio.sleep(600)  # 10 минут


class ProxyRouter(BaseProcessor):
    def __init__(
        self, context_manager: ContextManager, user_state_manager: UserStateManager
    ) -> None:
        super().__init__(
            context_manager=context_manager, user_state_manager=user_state_manager
        )
        self.proxies: set[Proxy] = set()

    def _get_proxy_by_name(self, name: str) -> Proxy | None:
        for p in list(self.proxies):
            if p.name == name:
                return p
        return None

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, ProxyState):
            if message.ready:
                self.proxies.add(message.proxy)
            else:
                self.proxies.discard(message.proxy)
            return []
        elif isinstance(message, ToPredict):
            if message.offer.identity.channel_type == ChannelType.tg:
                user_current_proxy_name = (
                    await self.user_state_manager.get_user_proxy_name(
                        chat_id=message.offer.identity.channel_id
                    )
                )
                proxy = self._get_proxy_by_name(name=user_current_proxy_name)
                if proxy is None:
                    proxy = self._get_proxy_by_name(name="ChatGPT-3.5 bounded")
            else:
                proxy = self._get_proxy_by_name(name="ChatGPT-3.5 bounded")
            if not proxy:
                raise Exception("Proxy not found")
            res = PreparedProxy(proxy=proxy, to_predict=message)  # TODO: check proxy
            return [res]
        return []


class PredictProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PreparedProxy):
            print(f"Start generate {message.proxy.name}")
            response_text = await message.proxy.generate(
                content=message.to_predict.context
            )
            print("End generate")
            res = PredictResult(offer=message.to_predict.offer, text=response_text)
            return [res]
        return []


class OutContextExist(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PredictResult):
            if message.offer.one_hit:
                res_gpt = GPTResult(identity=message.offer.identity, text=message.text)
                return [res_gpt]
            else:
                res = ToSaveContext(predict_result=message)
                return [res]
        return []


class ContextSaveProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, ToSaveContext):
            event_to_add = {"role": "assistant", "content": message.predict_result.text}
            await self.context_manager.add_event_in_context(
                user_id=message.predict_result.offer.identity.to_str, event=event_to_add
            )
            res = GPTResult(
                identity=message.predict_result.offer.identity,
                text=message.predict_result.text,
            )
            return [res]
        return []


class OutGPTResultRouter(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, GPTResult):
            if message.identity.channel_type == ChannelType.tg:
                res = OutTgResponse(identity=message.identity, text=message.text)
                print(res)
                return [res]
            elif message.identity.channel_type == ChannelType.api:
                res_api = OutAPIResponse(identity=message.identity, text=message.text)
                return [res_api]
            else:
                raise
        return []
