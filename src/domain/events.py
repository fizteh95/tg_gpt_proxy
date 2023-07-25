from dataclasses import dataclass

from src.domain.models import InputIdentity, Context


@dataclass
class PredictOffer:
    identity: InputIdentity
    text: None | str = None
    context: None | Context = None


@dataclass
class PredictOfferResolution:
    """Base class for auth resolutions"""


@dataclass
class PredictOfferResolutionAccept(PredictOfferResolution):
    offer: PredictOffer


@dataclass
class PredictOfferResolutionDecline(PredictOfferResolution):
    offer: PredictOffer
    reason: None | str = None
