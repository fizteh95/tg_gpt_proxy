from dataclasses import dataclass

from src.domain.models import Context
from src.domain.models import InputIdentity
from src.domain.models import Proxy


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
class OutResponse(Event):
    identity: InputIdentity
    text: str


@dataclass
class OutTgResponse(OutResponse):
    """Result text to tg"""


@dataclass
class OutAPIResponse(OutResponse):
    """Result text to api"""


@dataclass
class InTgText(Event):
    chat_id: str
    text: str


@dataclass
class InTgCommand(Event):
    chat_id: str
    command: str
