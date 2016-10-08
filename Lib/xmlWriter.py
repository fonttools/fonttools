# Added back here for backward compatibility

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fontTools.misc.xmlWriter import *
from fontTools.misc.xmlWriter import __doc__

import warnings

warnings.warn(
    "Importing the stand-alone `xmlWriter` module is deprecated. "
    "Use `from fontTools.misc import xmlWriter` instead.",
    stacklevel=2)
