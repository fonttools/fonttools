import logging
from fontTools.misc.loggingTools import configLogger

log = logging.getLogger(__name__)

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

version = __version__

__all__ = ["version", "log", "configLogger"]
