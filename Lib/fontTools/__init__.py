from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import logging
from fontTools.misc.loggingTools import Logger, configLogger

# set the logging.Logger class to one which supports the "last resort" handler,
# to be used when the client doesn't explicitly configure logging.
# It prints the bare message to sys.stderr, only for events of severity WARNING
# or greater.
logging.setLoggerClass(Logger)

log = logging.getLogger(__name__)

version = "3.0"

__all__ = ["version", "log", "configLogger"]
