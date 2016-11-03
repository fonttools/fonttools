from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import logging
from fontTools.misc.loggingTools import configLogger
from ._version import get_versions

log = logging.getLogger(__name__)

v = get_versions()
if v["error"]:
    __import__('warnings').warn("versioneer: %s" % v['error'], RuntimeWarning)
    __version__ = "3.2.1"
else:
    __version__ = v['version']
del get_versions, v

version = __version__

__all__ = ["version", "log", "configLogger"]
