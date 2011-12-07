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

__all__ = ["AbstractPointPen"]

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
