import DefaultTable
import Numeric
from fontTools import ttLib
from fontTools.misc.textTools import safeEval

superclass = ttLib.getTableClass("hmtx")

class table__v_m_t_x(superclass):
	
	headerTag = 'vhea'
	advanceName = 'height'
	sideBearingName = 'tsb'
	numberOfMetricsName = 'numberOfVMetrics'

