import asyncio
import random

import aiohttp

from src.domain.events import (
    Event,
    GPTResult,
    OutAPIResponse,
    OutTgResponse,
    PredictOffer,
    PredictOfferResolutionAccept,
    PredictResult,
    PreparedProxy,
    ProxyState,
    InTgText,
    ToPredict,
    ToRetrieveContext,
    ToSaveContext,
)
from src.domain.models import ChannelType, Context, InputIdentity, Proxy
from src.domain.subscriber import Subscriber
from src.services.message_bus import MessageBus


class BaseProcessor(Subscriber):
    def __init__(self) -> None:
        pass

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
    Класс для проверки, нужно ли вытаскивать контекст из БД
    """

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, ToRetrieveContext):
            identity_key = f"{message.offer.identity.channel_type.value}_{message.offer.identity.channel_id}"
            print(identity_key)
            # TODO: сделать выгрузку из БД
            ...
            if message.offer.text is None:
                raise
            context = [
                {"role": "user", "content": "Привет!"},
                {
                    "role": "assistant",
                    "content": "Йоу чувак, ваззаааап! С какой мазой тебе помочь сегодня?",
                },
                {"role": "user", "content": message.offer.text},
            ]
            res = ToPredict(offer=message.offer, context=Context(messages=context))
            return [res]
        return []


class ProxyChecker:
    """
    Загружает классы прокси из папки и периодически пингует их сообщениями
    """

    def __init__(self, bus: MessageBus) -> None:
        self.bus = bus

        class TestProxy(Proxy):
            def __init__(self, url: str, password: str | None = None) -> None:
                super().__init__(url=url, password=password)

            async def generate(self, content: Context) -> str:
                return "пампампам"

        self.proxies = [TestProxy(url="cuteanya")]

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
            await self.bus.public_message(message=res_list)
            # спим
            await asyncio.sleep(600)  # 10 минут


class ProxyRouter(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.proxies = set()

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
            # TODO: save in db
            ...
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
