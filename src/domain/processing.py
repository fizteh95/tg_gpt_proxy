import asyncio
import datetime

from src.domain.access_manager import AccessManager
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
from src.domain.events import PredictOfferResolutionDecline
from src.domain.events import PredictResult
from src.domain.events import PreparedProxy
from src.domain.events import ProxyState
from src.domain.events import TgBotTyping
from src.domain.events import TgEditText
from src.domain.events import ToPredict
from src.domain.events import ToRetrieveContext
from src.domain.events import ToSaveContext
from src.domain.models import ChannelType
from src.domain.models import Context
from src.domain.models import InputIdentity
from src.domain.models import TgInlineButton
from src.domain.models import TgInlineButtonArray
from src.domain.proxy_manager import ProxyManager
from src.domain.subscriber import Subscriber
from src.domain.user_state_manager import UserStateManager
from src.settings import logger


class BaseProcessor(Subscriber):
    def __init__(
        self,
        context_manager: ContextManager,
        user_state_manager: UserStateManager,
        access_manager: AccessManager,
        proxy_manager: ProxyManager,
    ) -> None:
        self.context_manager = context_manager
        self.user_state_manager = user_state_manager
        self.access_manager = access_manager
        self.proxy_manager = proxy_manager

    async def handle_message(self, message: Event) -> list[Event]:
        raise NotImplementedError


class Spy(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        logger.info(message)
        return []


class TgInProcessor(BaseProcessor):
    async def _text_processing(self, message: InTgText) -> list[Event]:
        identity = InputIdentity(
            channel_id=message.tg_user.chat_id, channel_type=ChannelType.tg
        )
        is_user_has_last_answer = await self.context_manager.is_user_has_last_answer(
            user_id=identity.to_str
        )
        if not is_user_has_last_answer:
            wait_res = OutTgResponse(
                identity=identity,
                text="Генерация ответа не завершена. Подожди пожалуйста.",
            )
            return [wait_res]
        res = PredictOffer(identity=identity, text=message.text, one_hit=False)
        return [res]

    async def _set_user_proxy_processing(self, identity: InputIdentity) -> list[Event]:
        proxy_list = await self.proxy_manager.get_proxy_properties(only_working=True)
        access_counter = await self.access_manager.get_access_counter(
            user_id=identity.to_str
        )
        user_current_proxy_name = await self.user_state_manager.get_user_proxy_name(
            chat_id=identity.channel_id
        )
        if not user_current_proxy_name:
            user_current_proxy_name = "ChatGPT-3.5 bounded"
        buttons: list[list[TgInlineButton]] = []
        res_text = "<b>Выберите прокси для общения:</b>\n\n"
        for e, p in enumerate(proxy_list):
            res_text += f"{e + 1}. {p['name']} - {p['description']}\n"
            if access_counter.remain_per_all_time <= 0 and p["premium"]:
                button_text = f"{e + 1}. 🔐 {p['name']}"
            else:
                if p["name"] == user_current_proxy_name:
                    button_text = f"✅ {e + 1}. {p['name']}"
                else:
                    button_text = f"{e + 1}. {p['name']}"
            buttons.append(
                [
                    TgInlineButton(
                        text=button_text,
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
            not_pushed_to_edit_text=f"Прокси не изменен. Текущий прокси: {user_current_proxy_name}",
        )
        return [res_proxy_choice]

    async def _command_processing(self, message: InTgCommand) -> list[Event]:
        identity = InputIdentity(
            channel_id=message.tg_user.chat_id, channel_type=ChannelType.tg
        )
        res_events: list[Event] = []
        created = await self.access_manager.create_access_counter_if_not_exists(
            user_id=identity.to_str
        )
        if created:
            created_notify_text = (
                "Новым пользователям доступно 10 запросов к бесплатным прокси. "
                "Чтобы увеличить лимиты и открыть заблокированные прокси, "
                "купите пакет запросов ;)"
            )
            created_notify = OutTgResponse(identity=identity, text=created_notify_text)
            res_events.append(created_notify)
        if message.command == "start":
            greeting = (
                "Привет! Это прокси до ChatGPT. Чтобы начать общаться, просто отправь сообщение ;)\n"
                "Команды бота:\n"
                "/clear - очистка контекста\n"
                "/set_proxy - переключение используемой модели\n"
                "/status - просмотр лимитов\n"
                "/buy - покупка доступа\n"
                "/help - показать список команд"
            )
            res_greet = OutTgResponse(identity=identity, text=greeting)
            res_events.insert(0, res_greet)
        elif message.command == "help":
            help_response = (
                "Команды бота:\n"
                "/clear - очистка контекста\n"
                "/set_proxy - переключение используемой модели\n"
                "/status - просмотр лимитов\n"
                "/buy - покупка доступа\n"
                "/help - показать список команд"
            )
            res_help = OutTgResponse(identity=identity, text=help_response)
            res_events.append(res_help)
        elif message.command == "clear":
            await self.context_manager.clear_context(user_id=identity.to_str)
            clear_response = "Контекст очищен."
            res_clear = OutTgResponse(identity=identity, text=clear_response)
            res_events.append(res_clear)
        # DEBUG command
        elif message.command == "buy":
            increase = 5
            await self.access_manager.increase_access_counter_premium(
                user_id=identity.to_str, count_increase=increase
            )
            increase_response = f"Промо-премиум режим увеличен на {increase} запросов"
            res_prem = OutTgResponse(identity=identity, text=increase_response)
            res_events.append(res_prem)
        elif message.command == "status":
            access_counter = await self.access_manager.get_access_counter(
                user_id=identity.to_str
            )
            if access_counter.remain_per_all_time > 0:
                limit_text = f"По платной подписке осталось {access_counter.remain_per_all_time} запросов."
            else:
                limit_text = (
                    f"На сегодня осталось {access_counter.remain_per_day} запросов. "
                    f"Счетчик обновится завтра."
                )
            res_limit = OutTgResponse(identity=identity, text=limit_text)
            res_events.append(res_limit)
        elif message.command == "set_proxy":
            res_proxy_choice = await self._set_user_proxy_processing(identity=identity)
            res_events += res_proxy_choice
        return res_events

    async def _button_processing(self, message: InTgButtonPushed) -> list[Event]:
        identity = InputIdentity(
            channel_id=message.tg_user.chat_id, channel_type=ChannelType.tg
        )
        if message.data.split()[0] == "proxy_choice":
            proxy_name = message.data[len(message.data.split()[0]) + 1 :]
            proxy_list = await self.proxy_manager.get_proxy_properties()
            access_counter = await self.access_manager.get_access_counter(
                user_id=identity.to_str
            )
            chosen_proxy = [x for x in proxy_list if x["name"] == proxy_name][0]
            if chosen_proxy["premium"] and access_counter.remain_per_all_time <= 0:
                edit_text = f"Прокси {proxy_name} вам недоступен, оплатите подписку чтобы открыть этот прокси)"
                edit_res = TgEditText(
                    identity=identity,
                    text=edit_text,
                    to_edit_like="proxy_choice_message",
                )
            else:
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

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, InTgText):
            return await self._text_processing(message=message)
        elif isinstance(message, InTgCommand):
            return await self._command_processing(message=message)
        elif isinstance(message, InTgButtonPushed):
            return await self._button_processing(message=message)
        return []


class AuthProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PredictOffer):
            events_to_bus: list[Event] = []
            created = await self.access_manager.create_access_counter_if_not_exists(
                user_id=message.identity.to_str
            )
            if created and message.identity.channel_type == ChannelType.tg:
                created_notify_text = (
                    "Новым пользователям доступно 10 запросов к бесплатным прокси. "
                    "Чтобы увеличить лимиты и открыть заблокированные прокси, "
                    "купите пакет запросов ;)"
                )
                created_notify = OutTgResponse(
                    identity=message.identity, text=created_notify_text
                )
                events_to_bus.append(created_notify)
            access_counter = await self.access_manager.get_access_counter(
                user_id=message.identity.to_str
            )
            if (
                access_counter.remain_per_day > 0
                or access_counter.remain_per_all_time > 0
            ):
                res = PredictOfferResolutionAccept(offer=message)
                events_to_bus.append(res)
                if message.identity.channel_type == ChannelType.tg:
                    typing_res = TgBotTyping(chat_id=message.identity.channel_id)
                    events_to_bus.append(typing_res)
            else:
                res = PredictOfferResolutionDecline(offer=message, reason="Закончился лимит на день(")  # type: ignore
                events_to_bus.append(res)
            return events_to_bus
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


class ProxyChecker(BaseProcessor):
    """
    Загружает классы прокси из папки и периодически пингует их сообщениями
    """

    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, ProxyState):
            if message.ready:
                await self.proxy_manager.make_proxy_working(message.proxy)
            else:
                await self.proxy_manager.make_proxy_not_working(message.proxy)
        return []

    async def start(self) -> None:
        # TODO: сделать по красоте
        while True:
            # working_proxies = []
            # not_working_proxies = []
            test_context = Context(
                messages=[{"role": "user", "content": "Привет, как дела?"}]
            )
            # проверка
            all_proxies = await self.proxy_manager.get_proxy_instances()
            for p in all_proxies:
                try:
                    res = await p.generate(content=test_context)
                    if isinstance(res, str) and len(res) > 0:
                        print(f"proxy working, {p}")
                        # working_proxies.append(p)
                        await self.proxy_manager.make_proxy_working(p)
                except Exception as e:
                    print(f"Proxy checker error: proxy={p.name}, error={e}")
                    # not_working_proxies.append(p)
                    await self.proxy_manager.make_proxy_not_working(p)
            # отправка результатов
            # res_list: list[Event] = []
            # for w in working_proxies:
            #     t1 = ProxyState(proxy=w, ready=True)
            #     res_list.append(t1)
            # for nw in not_working_proxies:
            #     t2 = ProxyState(proxy=nw, ready=False)
            #     res_list.append(t2)
            # print(f"proxy list: {res_list}")
            # await self.bus.public_message(message=res_list)
            # спим
            await asyncio.sleep(600)  # 10 минут


class AccessRefreshProcessor(BaseProcessor):
    def __init__(
        self,
        context_manager: ContextManager,
        user_state_manager: UserStateManager,
        access_manager: AccessManager,
        proxy_manager: ProxyManager,
    ) -> None:
        super().__init__(
            context_manager=context_manager,
            user_state_manager=user_state_manager,
            access_manager=access_manager,
            proxy_manager=proxy_manager,
        )
        self.updated_at = datetime.datetime.now()

    async def start(self) -> None:
        while True:
            now = datetime.datetime.now()
            if now.date() > self.updated_at.date():
                self.updated_at = datetime.datetime.now()
                await self.access_manager.refresh_access_counter_usual(count_level=10)
            # спим
            await asyncio.sleep(3600)  # час

    async def handle_message(self, message: Event) -> list[Event]:
        return []


class ProxyRouter(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        # if isinstance(message, ProxyState):
        #     if message.ready:
        #         self.proxies.add(message.proxy)
        #     else:
        #         self.proxies.discard(message.proxy)
        #     return []
        if isinstance(message, ToPredict):
            if message.offer.identity.channel_type == ChannelType.tg:
                user_current_proxy_name = (
                    await self.user_state_manager.get_user_proxy_name(
                        chat_id=message.offer.identity.channel_id
                    )
                )
                proxy = await self.proxy_manager.get_proxy_by_name(
                    name=user_current_proxy_name
                )
                if proxy is None:
                    proxy = await self.proxy_manager.get_default_proxy()
            else:
                proxy = await self.proxy_manager.get_default_proxy()
            if not proxy:
                raise Exception("Proxy not found")
            res = PreparedProxy(proxy=proxy, to_predict=message)  # TODO: check proxy
            return [res]
        return []


class PredictProcessor(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PreparedProxy):
            res: list[Event] = []
            print(f"Start generate {message.proxy.name}")
            try:
                response_text = await message.proxy.generate(
                    content=message.to_predict.context
                )
                print("End generate")
                pr = PredictResult(offer=message.to_predict.offer, text=response_text)
                res.append(pr)
            except Exception as e:
                logger.error(f"Proxy {message.proxy.name} not working! Error: {e}")
                await self.context_manager.pop_last_user_question(
                    user_id=message.to_predict.offer.identity.to_str
                )
                pr_error = OutTgResponse(
                    identity=message.to_predict.offer.identity,
                    text="Похоже, что прокси сломался( попробуй придти позже, "
                    "или выбери другой прокси командой /set_proxy.",
                )
                ps = ProxyState(proxy=message.proxy, ready=False)
                res += [pr_error, ps]
            return res
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
                events_to_bus: list[Event] = []
                res = OutTgResponse(identity=message.identity, text=message.text)
                print(res)
                events_to_bus.append(res)
                access_counter = await self.access_manager.get_access_counter(
                    user_id=message.identity.to_str
                )
                if access_counter.remain_per_all_time > 0:
                    is_zero = (
                        await self.access_manager.decrement_access_counter_premium(
                            user_id=message.identity.to_str
                        )
                    )
                    if is_zero:
                        free_proxy = await self.proxy_manager.get_default_proxy()
                        await self.user_state_manager.set_user_proxy_name(
                            chat_id=message.identity.channel_id,
                            proxy_name=free_proxy.name,
                        )
                        tg_notify_text = (
                            f"Закончился лимит на платные прокси. "
                            f"Для использования установлен бесплатный прокси {free_proxy.name}"
                        )
                        tg_notify_event = OutTgResponse(
                            identity=message.identity, text=tg_notify_text
                        )
                        events_to_bus.append(tg_notify_event)
                elif access_counter.remain_per_day > 0:
                    is_zero = await self.access_manager.decrement_access_counter_usual(
                        user_id=message.identity.to_str
                    )
                    if is_zero:
                        tg_notify_text = "Закончился дневной лимит на использование бота. Приходи завтра ;)"
                        tg_notify_event = OutTgResponse(
                            identity=message.identity, text=tg_notify_text
                        )
                        events_to_bus.append(tg_notify_event)
                return events_to_bus
            elif message.identity.channel_type == ChannelType.api:
                res_api = OutAPIResponse(identity=message.identity, text=message.text)
                return [res_api]
            else:
                raise
        return []


class ResolutionDeclineRouter(BaseProcessor):
    async def handle_message(self, message: Event) -> list[Event]:
        if isinstance(message, PredictOfferResolutionDecline):
            if message.offer.identity.channel_type == ChannelType.tg:
                res = OutTgResponse(
                    identity=message.offer.identity, text=message.reason
                )
                return [res]
            elif message.offer.identity.channel_type == ChannelType.api:
                res_api = OutAPIResponse(
                    identity=message.offer.identity, text=message.reason
                )
                return [res_api]
            else:
                raise
        return []
