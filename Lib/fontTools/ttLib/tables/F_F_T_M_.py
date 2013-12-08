from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from ._h_e_a_d import mac_epoch_diff
from . import DefaultTable
import time
import calendar

FFTMFormat = """
		>	# big endian
		version:        I
		FFTimeStamp:    Q
		sourceCreated:  Q
		sourceModified: Q
"""

class table_F_F_T_M_(DefaultTable.DefaultTable):

  def decompile(self, data, ttFont):
    dummy, rest = sstruct.unpack2(FFTMFormat, data, self)

  def compile(self, ttFont):
    data = sstruct.pack(FFTMFormat, self)
    return data

  def toXML(self, writer, ttFont):
    writer.comment("FontForge's timestamp, font source creation and modification dates")
    writer.newline()
    formatstring, names, fixes = sstruct.getformat(FFTMFormat)
    for name in names:
      value = getattr(self, name)
      if name in ("FFTimeStamp", "sourceCreated", "sourceModified"):
        try:
          value = time.asctime(time.gmtime(max(0, value + mac_epoch_diff)))
        except ValueError:
          value = time.asctime(time.gmtime(0))
      writer.simpletag(name, value=value)
      writer.newline()

  def fromXML(self, name, attrs, content, ttFont):
    value = attrs["value"]
    if name in ("FFTimeStamp", "sourceCreated", "sourceModified"):
      value = calendar.timegm(time.strptime(value)) - mac_epoch_diff
    else:
      value = safeEval(value)
    setattr(self, name, value)