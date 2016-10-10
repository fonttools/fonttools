from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import logging
from fontTools.misc.loggingTools import configLogger

log = logging.getLogger(__name__)

try:
    from fontTools.version import __version__
except ImportError:
    log.warning("The 'version.py' module is missing. "
                "Make sure FontTools is properly installed.")
    version = "0.0.0"
else:
    version = __version__

__all__ = ["version", "log", "configLogger"]
