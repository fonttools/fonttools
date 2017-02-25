from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import AbstractPen


__all__ = ["AbstractPen"]


class RecordingPen(AbstractPen):
	def __init__(self):
		self.value = []
	def moveTo(self, p0):
		self.value.append(('moveTo', (p0,)))
	def lineTo(self, p1):
		self.value.append(('lineTo', (p1,)))
	def qCurveTo(self, *points):
		self.value.append(('qCurveTo', points))
	def curveTo(self, *points):
		self.value.append(('curveTo', points))
	def closePath(self):
		self.value.append(('closePath', ()))
	def endPath(self):
		self.value.append(('endPath', ()))
	def addComponent(self, glyphName, transformation):
		self.value.append(('addComponent', (glyphName, transformation)))

	def replay(self, pen):
		for operator,operands in self.value:
			getattr(pen, operator)(*operands)


if __name__ == "__main__":
	from fontTools.pens.basePen import _TestPen
	pen = RecordingPen()
	pen.moveTo((0, 0))
	pen.lineTo((0, 100))
	pen.curveTo((50, 75), (60, 50), (50, 25))
	pen.closePath()
	from pprint import pprint
	pprint(pen.value)
