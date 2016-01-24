from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import logging

# add a do-nothing handler to the libary's top-level logger, to avoid
# "no handlers could be found" error if client doesn't configure logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# clients may call this to configure logging with a predefined handler and format
from fontTools.misc.loggingTools import configLogger

version = "3.0"

__all__ = ["version", "log", "configLogger"]
