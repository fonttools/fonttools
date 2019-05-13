from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import logging
from fontTools.misc.loggingTools import configLogger

log = logging.getLogger(__name__)

version = __version__ = "3.41.2"

__all__ = ["version", "log", "configLogger"]
