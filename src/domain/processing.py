import asyncio
import random

import aiohttp  # noqa

from src.domain.context_manager import ContextManager
from src.domain.events import Event
from src.domain.events import GPTResult
from src.domain.events import InTgText
from src.domain.events import OutAPIResponse
from src.domain.events import OutTgResponse
from src.domain.events import PredictOffer
from src.domain.events import PredictOfferResolutionAccept
from src.domain.events import PredictResult
from src.domain.events import PreparedProxy
from src.domain.events import ProxyState
from src.domain.events import ToPredict
from src.domain.events import ToRetrieveContext
from src.domain.events import ToSaveContext
from src.domain.models import ChannelType
from src.domain.models import Context
from src.domain.models import InputIdentity
from src.domain.models import Proxy
from src.domain.subscriber import Subscriber
from src.proxies.cuteanya import TestProxy
from src.proxies.new_test import NewTestProxy
from src.services.message_bus import MessageBus


class BaseProcessor(Subscriber):
    def __init__(self, context_manager: ContextManager) -> None:
        self.context_manager = context_manager

    async def handle_message(self, message: Event) -> list[Event]:
        raise NotImplementedError


class TgInProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, InTgText):
            identity = InputIdentity(
                channel_id=message.chat_id, channel_type=ChannelType.tg
            )
            res = PredictOffer(identity=identity, text=message.text, one_hit=False)
            return [res]
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
            res = ToPredict(offer=message.offer, context=context)
            return [res]
        return []


class ProxyChecker:
    """
    Загружает классы прокси из папки и периодически пингует их сообщениями
    """

    def __init__(self, bus: MessageBus) -> None:
        self.bus = bus
        # loading proxies
        first_proxy = NewTestProxy(url="new_test_proxy")
        second_proxy = TestProxy(url="cuteanya")
        self.proxies = [first_proxy, second_proxy]

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
                    print(f"Proxy checker error: proxy={p.url}, error={e}")
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
    def __init__(self, context_manager: ContextManager) -> None:
        super().__init__(context_manager=context_manager)
        self.proxies: set[Proxy] = set()

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, ProxyState):
            if message.ready:
                self.proxies.add(message.proxy)
            else:
                self.proxies.discard(message.proxy)
            return []
        elif isinstance(message, ToPredict):
            # TODO: make not random
            proxy = random.choice(list(self.proxies))
            res = PreparedProxy(proxy=proxy, to_predict=message)
            return [res]
        return []


class PredictProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PreparedProxy):
            response_text = await message.proxy.generate(
                content=message.to_predict.context
            )
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
