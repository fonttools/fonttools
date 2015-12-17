from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib

superclass = ttLib.getTableClass("TSI0")

class table_T_S_I__2(superclass):

	dependencies = ["TSI3"]
