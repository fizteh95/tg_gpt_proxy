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
    def __init__(self, url: str, password: str | None = None):
        self.url = url
        self.password = password

    @abstractmethod
    async def generate(self, content: Context) -> str:
        raise NotImplementedError
