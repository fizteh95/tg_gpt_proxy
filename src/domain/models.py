import enum
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class Context:
    messages: list[dict[str, str]]


class ChannelType(enum.Enum):
    tg = "Telegram"
    api = "API"


@dataclass
class InputIdentity:
    channel_type: ChannelType
    channel_id: str

    @property
    def to_str(self) -> str:
        return f"{self.channel_type.value}_{self.channel_id}"


class Proxy(ABC):
    def __init__(self) -> None:
        self.name = ""
        self.description = ""

    @abstractmethod
    async def generate(self, content: Context) -> str:
        raise NotImplementedError


@dataclass
class TgUser:
    chat_id: str
    username: str | None = None
    name: str | None = None
    surname: str | None = None


@dataclass
class AccessCounter:
    remain_per_day: int
    remain_per_all_time: int


class StateMap(enum.Enum):
    tg_state = "tg_state"
    current_proxy = "current_proxy"


class TgState(enum.Enum):
    usual_work = "usual_work"
    choose_proxy = "choose_proxy"


@dataclass
class TgInlineButton:
    text: str
    callback_data: str


@dataclass
class TgInlineButtonArray:
    buttons: list[list[TgInlineButton]]
