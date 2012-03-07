from robofab.world import RFont
from fontTools.pens.basePen import BasePen
from robofab.misc.arrayTools import updateBounds, pointInRect, unionRect
from robofab.misc.bezierTools import calcCubicBounds, calcQuadraticBounds
from robofab.pens.filterPen import _estimateCubicCurveLength, _getCubicPoint
import math



__all__ = ["AngledMarginPen", "getAngledMargins", 
	"setAngledLeftMargin", "setAngledRightMargin",
	"centerAngledMargins"]



class AngledMarginPen(BasePen):
	"""
		Pen to calculate the margins according to a slanted coordinate system. Slant angle comes from font.info.italicAngle.

			- this pen works on the on-curve points, and approximates the distance to curves.
			- results will be float.
			- when used in FontLab, the resulting margins may be slightly different from the values originally set, due to rounding errors.

			Notes:

			- similar to what RoboFog used to do.
			- RoboFog had a special attribute for "italicoffset", horizontal shift of all glyphs. This is missing in Robofab.
	"""
	def __init__(self, glyphSet, width, italicAngle):
		BasePen.__init__(self, glyphSet)
		self.width = width
		self._angle = math.radians(90+italicAngle)
		self.maxSteps = 100
		self.margin = None
		self._left = None
		self._right = None
		self._start = None
		self.currentPt = None
	
	def _getAngled(self, pt):
		print "_getAngled", pt
		r = (self.width + (pt[1] / math.tan(self._angle)))-pt[0]
		l = pt[0]-((pt[1] / math.tan(self._angle)))
		if self._right is None:
			self._right = r
		else:
			self._right = min(self._right, r)
		if self._left is None:
			self._left = l
		else:
			self._left = min(self._left, l)
		self.margin = self._left, self._right
		
	def _moveTo(self, pt):
		self._start = self.currentPt = pt

	def _addMoveTo(self):
		if self._start is None:
			return
		self._start = self.currentPt = None

	def _lineTo(self, pt):
		self._addMoveTo()
		print "_lineTo"
		self._getAngled(pt)

	def _curveToOne(self, pt1, pt2, pt3):
		step = 1.0/self.maxSteps
		factors = range(0, self.maxSteps+1)
		for i in factors:
			print "_curveToOne", i
			pt = _getCubicPoint(i*step, self.currentPt, pt1, pt2, pt3)
			self._getAngled(pt)
		self.currentPt = pt3
					
	def _qCurveToOne(self, bcp, pt):
		self._addMoveTo()
		# add curve tracing magic here.
		print "_qCurveToOne"
		self._getAngled(pt)
		self.currentPt = pt3

def getAngledMargins(glyph, font):
	"""Convenience function, returns the angled margins for this glyph. Adjusted for font.info.italicAngle."""
	pen = AngledMarginPen(font, glyph.width, font.info.italicAngle)
	glyph.draw(pen)
	return pen.margin
	
def setAngledLeftMargin(glyph, font, value):
	"""Convenience function, sets the left angled margin to value. Adjusted for font.info.italicAngle."""
	pen = AngledMarginPen(font, glyph.width, font.info.italicAngle)
	g.draw(pen)
	isLeft, isRight = pen.margin
	glyph.leftMargin += value-isLeft
	
def setAngledRightMargin(glyph, font, value):
	"""Convenience function, sets the right angled margin to value. Adjusted for font.info.italicAngle."""
	pen = AngledMarginPen(font, glyph.width, font.info.italicAngle)
	g.draw(pen)
	isLeft, isRight = pen.margin
	glyph.rightMargin += value-isRight

def centerAngledMargins(glyph, font):
	"""Convenience function, centers the glyph on angled margins."""
	pen = AngledMarginPen(font, glyph.width, font.info.italicAngle)
	g.draw(pen)
	isLeft, isRight = pen.margin
	setAngledLeftMargin(glyph, font, (isLeft+isRight)*.5)
	setAngledRightMargin(glyph, font, (isLeft+isRight)*.5)
	
def guessItalicOffset(glyph, font):
	"""Guess the italic offset based on the margins of a symetric glyph.
		For instance H or I.
	"""
	l, r = getAngledMargins(glyph, font)
	return l - (l+r)*.5


if __name__ == "__main__":

	def makeTestGlyph():
		# make a simple glyph that we can test the pens with.
		from robofab.objects.objectsRF import RGlyph
		testGlyph = RGlyph()
		testGlyph.name = "testGlyph"
		testGlyph.width = 1000
		pen = testGlyph.getPen()
		pen.moveTo((100, 100))
		pen.lineTo((900, 100))
		pen.lineTo((900, 800))
		pen.lineTo((100, 800))
		# a curve
		pen.curveTo((120, 700), (120, 300), (100, 100))
		pen.closePath()
		return testGlyph

	def angledMarginPenTest():
		testGlyph = makeTestGlyph()
		glyphSet = {}
		testPen = AngledMarginPen(glyphSet, width=0, italicAngle=10)
		testGlyph.draw(testPen)
		print testPen.margin

	angledMarginPenTest()