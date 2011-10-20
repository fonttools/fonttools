"""
=============================
Filters: chaining pen objects
=============================

By chaining two (or more) pen objects together, the first pen can function as a filter to the second. The first pen receives data from (for instance) glyph.draw() or glyph.drawPoints(). The filter pen then processes the data and passes new, fresh data to the second pen. In turn the second pen can draw in a glyph. 

Filterpens need to be initialised with a second pen object that will receive the processed data. The examples in this module, ThresholdPen and FlattenPen, have proven useful in a number of projects. For convenienve, each pen has a wrapper function that takes care of making a new glyph to dump the processed data in, and making the appropriate pen instances. But these are non-normative examples.

All pens in this module subclass from fontTools.pens.basePen.

"""


from fontTools.pens.basePen import AbstractPen, BasePen



from ufoLib.pointPen import AbstractPointPen
from robofab.objects.objectsRF import RGlyph as _RGlyph
from robofab.objects.objectsBase import _interpolatePt

import math


#
#	 threshold filtering
#

def distance(pt1, pt2):
	return math.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)


class ThresholdPen(AbstractPen):

	"""This pen only draws segments longer in length than the threshold value.	

		- otherPen: a different segment pen object this filter should draw the results with.
		- threshold: the minimum length of a segment
	"""

	def __init__(self, otherPen, threshold=10):
		self.threshold = threshold
		self._lastPt = None
		self.otherPen = otherPen

	def moveTo(self, pt):
		self._lastPt = pt
		self.otherPen.moveTo(pt)
	
	def lineTo(self, pt, smooth=False):
		if self.threshold <= distance(pt, self._lastPt):
			self.otherPen.lineTo(pt)
			self._lastPt = pt
		
	def curveTo(self, pt1, pt2, pt3):
		if self.threshold <= distance(pt3, self._lastPt):
			self.otherPen.curveTo(pt1, pt2, pt3)
			self._lastPt = pt3

	def qCurveTo(self, *points):
		if self.threshold <= distance(points[-1], self._lastPt):
			self.otherPen.qCurveTo(*points)
			self._lastPt = points[-1]
		
	def closePath(self):
		self.otherPen.closePath()
	
	def endPath(self):
		self.otherPen.endPath()
		
	def addComponent(self, glyphName, transformation):
		self.otherPen.addComponent(glyphName, transformation)


def thresholdGlyph(aGlyph, threshold=10):
	
	"""Convenience function that applies the **ThresholdPen** to a glyph. Returns a new glyph object (from objectsRF.RGlyph)."""
	
	from robofab.pens.adapterPens import PointToSegmentPen
	new = _RGlyph()
	filterpen = ThresholdPen(new.getPen(), threshold)
	wrappedPen = PointToSegmentPen(filterpen)
	aGlyph.drawPoints(wrappedPen)
	aGlyph.clear()
	aGlyph.appendGlyph(new)
	aGlyph.update()
	return aGlyph
	
#
# Curve flattening
#

def _estimateCubicCurveLength(pt0, pt1, pt2, pt3, precision=10):
	"""Estimate the length of this curve by iterating
	through it and averaging the length of the flat bits.
	"""
	points = []
	length = 0
	step = 1.0/precision
	factors = range(0, precision+1)
	for i in factors:
		points.append(_getCubicPoint(i*step, pt0, pt1, pt2, pt3))
	for i in range(len(points)-1):
		pta = points[i]
		ptb = points[i+1]
		length += distance(pta, ptb)
	return length

def _mid((x0, y0), (x1, y1)):
	"""(Point, Point) -> Point\nReturn the point that lies in between the two input points."""
	return 0.5 * (x0 + x1), 0.5 * (y0 + y1)

def _getCubicPoint(t, pt0, pt1, pt2, pt3):
	if t == 0:
		return pt0
	if t == 1:
		return pt3
	if t == 0.5:
		a = _mid(pt0, pt1)
		b = _mid(pt1, pt2)
		c = _mid(pt2, pt3)
		d = _mid(a, b)
		e = _mid(b, c)
		return _mid(d, e)
	else:
		cx = (pt1[0] - pt0[0]) * 3
		cy = (pt1[1] - pt0[1]) * 3
		bx = (pt2[0] - pt1[0]) * 3 - cx
		by = (pt2[1] - pt1[1]) * 3 - cy
		ax = pt3[0] - pt0[0] - cx - bx
		ay = pt3[1] - pt0[1] - cy - by
		t3 = t ** 3
		t2 = t * t
		x = ax * t3 + bx * t2 + cx * t + pt0[0]
		y = ay * t3 + by * t2 + cy * t + pt0[1]
		return x, y


class FlattenPen(BasePen):

	"""This filter pen processes the contours into a series of straight lines by flattening the curves.
	
		- otherPen: a different segment pen object this filter should draw the results with.
		- approximateSegmentLength: the length you want the flattened segments to be (roughly).
		- segmentLines: whether to cut straight lines into segments as well.
		- filterDoubles: don't draw if a segment goes to the same coordinate.
	"""

	def __init__(self, otherPen, approximateSegmentLength=5, segmentLines=False, filterDoubles=True):
		self.approximateSegmentLength = approximateSegmentLength
		BasePen.__init__(self, {})
		self.otherPen = otherPen
		self.currentPt = None
		self.firstPt = None
		self.segmentLines = segmentLines
		self.filterDoubles = filterDoubles

	def _moveTo(self, pt):
		self.otherPen.moveTo(pt)
		self.currentPt = pt
		self.firstPt = pt

	def _lineTo(self, pt):
		if self.filterDoubles:
			if pt == self.currentPt:
				return
		if not self.segmentLines:
			self.otherPen.lineTo(pt)
			self.currentPt = pt
			return
		d = distance(self.currentPt, pt)
		maxSteps = int(round(d / self.approximateSegmentLength))
		if maxSteps < 1:
			self.otherPen.lineTo(pt)
			self.currentPt = pt
			return
		step = 1.0/maxSteps
		factors = range(0, maxSteps+1)
		for i in factors[1:]:
			self.otherPen.lineTo(_interpolatePt(self.currentPt, pt, i*step))
		self.currentPt = pt

	def _curveToOne(self, pt1, pt2, pt3):
		est = _estimateCubicCurveLength(self.currentPt, pt1, pt2, pt3)/self.approximateSegmentLength
		maxSteps = int(round(est))
		falseCurve = (pt1==self.currentPt) and (pt2==pt3)
		if maxSteps < 1 or falseCurve:
			self.otherPen.lineTo(pt3)
			self.currentPt = pt3
			return
		step = 1.0/maxSteps
		factors = range(0, maxSteps+1)
		for i in factors[1:]:
			pt = _getCubicPoint(i*step, self.currentPt, pt1, pt2, pt3)
			self.otherPen.lineTo(pt)
		self.currentPt = pt3
		
	def _closePath(self):
		self.lineTo(self.firstPt)
		self.otherPen.closePath()
		self.currentPt = None
	
	def _endPath(self):
		self.otherPen.endPath()
		self.currentPt = None
		
	def addComponent(self, glyphName, transformation):
		self.otherPen.addComponent(glyphName, transformation)


def flattenGlyph(aGlyph, threshold=10, segmentLines=True):

	"""Convenience function that applies the **FlattenPen** pen to a glyph. Returns a new glyph object."""

	from robofab.pens.adapterPens import PointToSegmentPen
	if len(aGlyph.contours) == 0:
		return
	new = _RGlyph()
	writerPen = new.getPen()
	filterpen = FlattenPen(writerPen, threshold, segmentLines)
	wrappedPen = PointToSegmentPen(filterpen)
	aGlyph.drawPoints(wrappedPen)
	aGlyph.clear()
	aGlyph.appendGlyph(new)
	aGlyph.update()
	return aGlyph

