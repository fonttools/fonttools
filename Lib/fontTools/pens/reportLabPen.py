from fontTools.pens.basePen import BasePen


class ReportLabPen(BasePen):

	"""A pen for drawing onto a reportlab.graphics.shapes.Path object."""

	def __init__(self, glyphSet, path=None):
		BasePen.__init__(self, glyphSet)
		if path is None:
			from reportlab.graphics.shapes import Path
			path = Path()
		self.path = path

	def _moveTo(self, (x,y)):
		self.path.moveTo(x,y)

	def _lineTo(self, (x,y)):
		self.path.lineTo(x,y)

	def _curveToOne(self, (x1,y1), (x2,y2), (x3,y3)):
		self.path.curveTo(x1, y1, x2, y2, x3, y3)

	def _closePath(self):
		self.path.closePath()


if __name__=="__main__":
	import sys
	if len(sys.argv) < 3:
		print "Usage: reportLabPen.py <OTF/TTF font> <glyphname> [<image file to create>]"
		print "  If no image file name is created, by default <glyphname>.png is created."
		print "  example: reportLabPen.py Arial.TTF R test.png"
		print "  (The file format will be PNG, regardless of the image file name supplied)"
		sys.exit(0)

	from fontTools.ttLib import TTFont
	from reportlab.lib import colors
	from reportlab.graphics.shapes import Path

	path = sys.argv[1]
	glyphName = sys.argv[2]
	if (len(sys.argv) > 3):
		imageFile = sys.argv[3]
	else:
		imageFile = "%s.png" % glyphName

	font = TTFont(path)  # it would work just as well with fontTools.t1Lib.T1Font
	gs = font.getGlyphSet()
	pen = ReportLabPen(gs, Path(fillColor=colors.red, strokeWidth=5))
	g = gs[glyphName]
	g.draw(pen)

	w, h = g.width, 1000
	from reportlab.graphics import renderPM
	from reportlab.graphics.shapes import Group, Drawing, scale

	# Everything is wrapped in a group to allow transformations.
	g = Group(pen.path)
	g.translate(0, 200)
	g.scale(0.3, 0.3)

	d = Drawing(w, h)
	d.add(g)

	renderPM.drawToFile(d, imageFile, fmt="PNG")
