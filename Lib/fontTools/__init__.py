import logging
from fontTools.misc.loggingTools import configLogger

log = logging.getLogger(__name__)

version = __version__ = "4.33.2"

__all__ = ["version", "log", "configLogger"]
