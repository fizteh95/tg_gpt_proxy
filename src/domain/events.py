from dataclasses import dataclass

from src.domain.models import Context
from src.domain.models import InputIdentity
from src.domain.models import Proxy
from src.domain.models import TgInlineButtonArray
from src.domain.models import TgUser


@dataclass
class Event:
    """Base class for events"""


@dataclass
class PredictOffer(Event):
    identity: InputIdentity
    text: None | str = None
    context: None | Context = None
    one_hit: bool = True


@dataclass
class PredictOfferResolution(Event):
    """Base class for auth resolutions"""


@dataclass
class PredictOfferResolutionAccept(PredictOfferResolution):
    offer: PredictOffer


@dataclass
class PredictOfferResolutionDecline(PredictOfferResolution):
    offer: PredictOffer
    reason: str


@dataclass
class ToRetrieveContext(Event):
    offer: PredictOffer


@dataclass
class ToPredict(Event):
    offer: PredictOffer
    context: Context


@dataclass
class ProxyState(Event):
    proxy: Proxy
    ready: bool


@dataclass
class PreparedProxy(Event):
    proxy: Proxy
    to_predict: ToPredict


@dataclass
class PredictResult(Event):
    offer: PredictOffer
    text: str


@dataclass
class ToSaveContext(Event):
    predict_result: PredictResult


@dataclass
class GPTResult(Event):
    identity: InputIdentity
    text: str


@dataclass
class OutResponse(Event):
    identity: InputIdentity
    text: str


@dataclass
class OutTgResponse(OutResponse):
    """Result text to tg"""

    inline_buttons: TgInlineButtonArray | None = None
    to_save_like: str = ""
    not_pushed_to_delete: bool = False
    not_pushed_to_edit_text: str = ""


@dataclass
class OutAPIResponse(OutResponse):
    """Result text to api"""


@dataclass
class InTgText(Event):
    tg_user: TgUser
    text: str


@dataclass
class InTgCommand(Event):
    tg_user: TgUser
    command: str


@dataclass
class InTgButtonPushed(Event):
    tg_user: TgUser
    data: str


@dataclass
class TgEditText(Event):
    identity: InputIdentity
    to_edit_like: str
    text: str
    inline_buttons: TgInlineButtonArray | None = None
    message_id: str | None = None


@dataclass
class MessageToDelete(Event):
    chat_id: str
    message_id: str


@dataclass
class TgBotTyping(Event):
    chat_id: str
