# Added here for backward compatibility

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fontTools.misc.sstruct import *
from fontTools.misc.sstruct import __doc__

import warnings

warnings.warn(
    "Importing the stand-alone `sstruct` module is deprecated. "
    "Use `from fontTools.misc import sstruct` instead.",
    stacklevel=2)
