"""Pen recording operations that can be accessed or replayed."""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import AbstractPen, DecomposingPen


__all__ = ["replayRecording", "RecordingPen", "DecomposingRecordingPen"]


def replayRecording(recording, pen):
	"""Replay a recording, as produced by RecordingPen or DecomposingRecordingPen,
	to a pen.

	Note that recording does not have to be produced by those pens.
	It can be any iterable of tuples of method name and tuple-of-arguments.
	Likewise, pen can be any objects receiving those method calls.
	"""
	for operator,operands in recording:
		getattr(pen, operator)(*operands)


class RecordingPen(AbstractPen):
	"""Pen recording operations that can be accessed or replayed.

	The recording can be accessed as pen.value; or replayed using
	pen.replay(otherPen).

	Usage example:
	==============
	from fontTools.ttLib import TTFont
	from fontTools.pens.recordingPen import RecordingPen

	glyph_name = 'dollar'
	font_path = 'MyFont.otf'

	font = TTFont(font_path)
	glyphset = font.getGlyphSet()
	glyph = glyphset[glyph_name]

	pen = RecordingPen()
	glyph.draw(pen)
	print(pen.value)
	"""

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
		replayRecording(self.value, pen)


class DecomposingRecordingPen(DecomposingPen, RecordingPen):
	""" Same as RecordingPen, except that it doesn't keep components
	as references, but draws them decomposed as regular contours.

	The constructor takes a single 'glyphSet' positional argument,
	a dictionary of glyph objects (i.e. with a 'draw' method) keyed
	by thir name.

	>>> class SimpleGlyph(object):
	...     def draw(self, pen):
	...         pen.moveTo((0, 0))
	...         pen.curveTo((1, 1), (2, 2), (3, 3))
	...         pen.closePath()
	>>> class CompositeGlyph(object):
	...     def draw(self, pen):
	...         pen.addComponent('a', (1, 0, 0, 1, -1, 1))
	>>> glyphSet = {'a': SimpleGlyph(), 'b': CompositeGlyph()}
	>>> for name, glyph in sorted(glyphSet.items()):
	...     pen = DecomposingRecordingPen(glyphSet)
	...     glyph.draw(pen)
	...     print("{}: {}".format(name, pen.value))
	a: [('moveTo', ((0, 0),)), ('curveTo', ((1, 1), (2, 2), (3, 3))), ('closePath', ())]
	b: [('moveTo', ((-1, 1),)), ('curveTo', ((0, 2), (1, 3), (2, 4))), ('closePath', ())]
	"""
	# raises KeyError if base glyph is not found in glyphSet
	skipMissingComponents = False


if __name__ == "__main__":
	from fontTools.pens.basePen import _TestPen
	pen = RecordingPen()
	pen.moveTo((0, 0))
	pen.lineTo((0, 100))
	pen.curveTo((50, 75), (60, 50), (50, 25))
	pen.closePath()
	from pprint import pprint
	pprint(pen.value)
