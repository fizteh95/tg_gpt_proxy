import logging.config

from .base import *  # noqa
from .local import *  # noqa

logging.config.dictConfig(LOGGING)  # noqa
