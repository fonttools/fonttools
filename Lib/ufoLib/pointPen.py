"""
=========
PointPens
=========

Where **SegmentPens** have an intuitive approach to drawing
(if you're familiar with postscript anyway), the **PointPen**
is geared towards accessing all the data in the contours of
the glyph. A PointsPen has a very simple interface, it just
steps through all the points in a call from glyph.drawPoints().
This allows the caller to provide more data for each point.
For instance, whether or not a point is smooth, and its name.
"""
from fontTools.pens.basePen import AbstractPen

__all__ = ["AbstractPointPen", "BasePointToSegmentPen", "PointToSegmentPen",
		   "SegmentToPointPen"]


class AbstractPointPen(object):
	"""
	Baseclass for all PointPens.
	"""

	def beginPath(self):
		"""Start a new sub path."""
		raise NotImplementedError

	def endPath(self):
		"""End the current sub path."""
		raise NotImplementedError

	def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
		"""Add a point to the current sub path."""
		raise NotImplementedError

	def addComponent(self, baseGlyphName, transformation):
		"""Add a sub glyph."""
		raise NotImplementedError


class BasePointToSegmentPen(AbstractPointPen):
	"""
	Base class for retrieving the outline in a segment-oriented
	way. The PointPen protocol is simple yet also a little tricky,
	so when you need an outline presented as segments but you have
	as points, do use this base implementation as it properly takes
	care of all the edge cases.
	"""

	def __init__(self):
		self.currentPath = None

	def beginPath(self, **kwargs):
		assert self.currentPath is None
		self.currentPath = []

	def _flushContour(self, segments):
		"""Override this method.

		It will be called for each non-empty sub path with a list
		of segments: the 'segments' argument.

		The segments list contains tuples of length 2:
			(segmentType, points)

		segmentType is one of "move", "line", "curve" or "qcurve".
		"move" may only occur as the first segment, and it signifies
		an OPEN path. A CLOSED path does NOT start with a "move", in
		fact it will not contain a "move" at ALL.

		The 'points' field in the 2-tuple is a list of point info
		tuples. The list has 1 or more items, a point tuple has
		four items:
			(point, smooth, name, kwargs)
		'point' is an (x, y) coordinate pair.

		For a closed path, the initial moveTo point is defined as
		the last point of the last segment.

		The 'points' list of "move" and "line" segments always contains
		exactly one point tuple.
		"""
		raise NotImplementedError

	def endPath(self):
		assert self.currentPath is not None
		points = self.currentPath
		self.currentPath = None
		if not points:
			return
		if len(points) == 1:
			# Not much more we can do than output a single move segment.
			pt, segmentType, smooth, name, kwargs = points[0]
			segments = [("move", [(pt, smooth, name, kwargs)])]
			self._flushContour(segments)
			return
		segments = []
		if points[0][1] == "move":
			# It's an open contour, insert a "move" segment for the first
			# point and remove that first point from the point list.
			pt, segmentType, smooth, name, kwargs = points[0]
			segments.append(("move", [(pt, smooth, name, kwargs)]))
			points.pop(0)
		else:
			# It's a closed contour. Locate the first on-curve point, and
			# rotate the point list so that it _ends_ with an on-curve
			# point.
			firstOnCurve = None
			for i in range(len(points)):
				segmentType = points[i][1]
				if segmentType is not None:
					firstOnCurve = i
					break
			if firstOnCurve is None:
				# Special case for quadratics: a contour with no on-curve
				# points. Add a "None" point. (See also the Pen protocol's
				# qCurveTo() method and fontTools.pens.basePen.py.)
				points.append((None, "qcurve", None, None, None))
			else:
				points = points[firstOnCurve+1:] + points[:firstOnCurve+1]

		currentSegment = []
		for pt, segmentType, smooth, name, kwargs in points:
			currentSegment.append((pt, smooth, name, kwargs))
			if segmentType is None:
				continue
			segments.append((segmentType, currentSegment))
			currentSegment = []

		self._flushContour(segments)

	def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
		self.currentPath.append((pt, segmentType, smooth, name, kwargs))


class PointToSegmentPen(BasePointToSegmentPen):
	"""
	Adapter class that converts the PointPen protocol to the
	(Segment)Pen protocol.
	"""

	def __init__(self, segmentPen, outputImpliedClosingLine=False):
		BasePointToSegmentPen.__init__(self)
		self.pen = segmentPen
		self.outputImpliedClosingLine = outputImpliedClosingLine

	def _flushContour(self, segments):
		assert len(segments) >= 1
		pen = self.pen
		if segments[0][0] == "move":
			# It's an open path.
			closed = False
			points = segments[0][1]
			assert len(points) == 1
			movePt, smooth, name, kwargs = points[0]
			del segments[0]
		else:
			# It's a closed path, do a moveTo to the last
			# point of the last segment.
			closed = True
			segmentType, points = segments[-1]
			movePt, smooth, name, kwargs = points[-1]
		if movePt is None:
			# quad special case: a contour with no on-curve points contains
			# one "qcurve" segment that ends with a point that's None. We
			# must not output a moveTo() in that case.
			pass
		else:
			pen.moveTo(movePt)
		outputImpliedClosingLine = self.outputImpliedClosingLine
		nSegments = len(segments)
		for i in range(nSegments):
			segmentType, points = segments[i]
			points = [pt for pt, smooth, name, kwargs in points]
			if segmentType == "line":
				assert len(points) == 1
				pt = points[0]
				if i + 1 != nSegments or outputImpliedClosingLine or not closed:
					pen.lineTo(pt)
			elif segmentType == "curve":
				pen.curveTo(*points)
			elif segmentType == "qcurve":
				pen.qCurveTo(*points)
			else:
				assert 0, "illegal segmentType: %s" % segmentType
		if closed:
			pen.closePath()
		else:
			pen.endPath()

	def addComponent(self, glyphName, transform):
		self.pen.addComponent(glyphName, transform)


class SegmentToPointPen(AbstractPen):
	"""
	Adapter class that converts the (Segment)Pen protocol to the
	PointPen protocol.
	"""

	def __init__(self, pointPen, guessSmooth=True):
		if guessSmooth:
			self.pen = GuessSmoothPointPen(pointPen)
		else:
			self.pen = pointPen
		self.contour = None

	def _flushContour(self):
		pen = self.pen
		pen.beginPath()
		for pt, segmentType in self.contour:
			pen.addPoint(pt, segmentType=segmentType)
		pen.endPath()

	def moveTo(self, pt):
		self.contour = []
		self.contour.append((pt, "move"))

	def lineTo(self, pt):
		self.contour.append((pt, "line"))

	def curveTo(self, *pts):
		for pt in pts[:-1]:
			self.contour.append((pt, None))
		self.contour.append((pts[-1], "curve"))

	def qCurveTo(self, *pts):
		if pts[-1] is None:
			self.contour = []
		for pt in pts[:-1]:
			self.contour.append((pt, None))
		if pts[-1] is not None:
			self.contour.append((pts[-1], "qcurve"))

	def closePath(self):
		if len(self.contour) > 1 and self.contour[0][0] == self.contour[-1][0]:
			self.contour[0] = self.contour[-1]
			del self.contour[-1]
		else:
			# There's an implied line at the end, replace "move" with "line"
			# for the first point
			pt, tp = self.contour[0]
			if tp == "move":
				self.contour[0] = pt, "line"
		self._flushContour()
		self.contour = None

	def endPath(self):
		self._flushContour()
		self.contour = None

	def addComponent(self, glyphName, transform):
		assert self.contour is None
		self.pen.addComponent(glyphName, transform)
