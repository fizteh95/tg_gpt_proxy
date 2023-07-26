import enum
from abc import ABC, abstractmethod
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


class Proxy(ABC):
    def __init__(self, url: str, password: str | None = None):
        self.url = url
        self.password = password

    @abstractmethod
    def generate(self, content: Context) -> str:
        raise NotImplementedError
