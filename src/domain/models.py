from dataclasses import dataclass


@dataclass
class Context:
    messages: list[dict[str, str]]


@dataclass
class InputIdentity:
    channel_type: str
    channel_id: str