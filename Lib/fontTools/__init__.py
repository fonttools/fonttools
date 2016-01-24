from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import logging

# add a do-nothing handler to the libary's top-level logger, to avoid
# "no handlers could be found" error if client doesn't configure logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

version = "3.0"
