from robofab.pens.pointPen import AbstractPointPen, BasePointToSegmentPen

"""
	
	Printing pens print their data. Useful for demos and debugging.

"""

__all__ = ["PrintingPointPen", "PrintingSegmentPen", "SegmentPrintingPointPen"]

class PrintingPointPen(AbstractPointPen):
	"""A PointPen that prints every step.
	"""

	def __init__(self):
		self.havePath = False

	def beginPath(self):
		self.havePath = True
		print "pen.beginPath()"

	def endPath(self):
		self.havePath = False
		print "pen.endPath()"

	def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
		assert self.havePath
		args = ["(%s, %s)" % (pt[0], pt[1])]
		if segmentType is not None:
			args.append("segmentType=%r" % segmentType)
		if smooth:
			args.append("smooth=True")
		if name is not None:
			args.append("name=%r" % name)
		if kwargs:
			args.append("**%s" % kwargs)
		print "pen.addPoint(%s)" % ", ".join(args)

	def addComponent(self, baseGlyphName, transformation):
		assert not self.havePath
		print "pen.addComponent(%r, %s)" % (baseGlyphName, tuple(transformation))


from fontTools.pens.basePen import AbstractPen

class PrintingSegmentPen(AbstractPen):
	"""A SegmentPen that prints every step.
	"""
    
	def moveTo(self, pt):
		print "pen.moveTo(%s)" % (pt,)

	def lineTo(self, pt):
		print "pen.lineTo(%s)" % (pt,)

	def curveTo(self, *pts):
		print "pen.curveTo%s" % (pts,)

	def qCurveTo(self, *pts):
		print "pen.qCurveTo%s" % (pts,)

	def closePath(self):
		print "pen.closePath()"

	def endPath(self):
		print "pen.endPath()"

	def addComponent(self, baseGlyphName, transformation):
		print "pen.addComponent(%r, %s)" % (baseGlyphName, tuple(transformation))


class SegmentPrintingPointPen(BasePointToSegmentPen):
	"""A SegmentPen that pprints every step.
	"""
	def _flushContour(self, segments):
		from pprint import pprint
		pprint(segments)


if __name__ == "__main__":
	p = SegmentPrintingPointPen()
	from robofab.test.test_pens import TestShapes
	TestShapes.onCurveLessQuadShape(p)
