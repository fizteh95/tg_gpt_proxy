from dataclasses import dataclass

from src.domain.models import Context, InputIdentity, Proxy


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
    reason: None | str = None


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
class OutTgResponse(Event):
    """Result text to tg"""

    identity: InputIdentity
    text: str


@dataclass
class OutAPIResponse(Event):
    """Result text to api"""

    identity: InputIdentity
    text: str


@dataclass
class TgText(Event):
    chat_id: str
    text: str


@dataclass
class OutTgText(Event):
    chat_id: str
    text: str
