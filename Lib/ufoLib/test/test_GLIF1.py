import unittest
from ufoLib.glifLib import GlifLibError, readGlyphFromString, writeGlyphToString

# -----------------
# Glyph and Support
# -----------------

class Glyph(object):

	def __init__(self):
		self.name = None
		self.width = None
		self.height = None
		self.unicodes = None
		self.note = None
		self.image = None
		self.guidelines = None
		self.outline = []

	def _writePointPenCommand(self, command, args, kwargs):
		if args and kwargs:
			return "pointPen.%s(*%s, **%s)" % (command, listToString(args), dictToString(kwargs))
		elif args:
			return "pointPen.%s(*%s)" % (command, listToString(args))
		elif kwargs:
			return "pointPen.%s(**%s)" % (command, dictToString(kwargs))
		else:
			return "pointPen.%s()" % command

	def beginPath(self, **kwargs):
		self.outline.append(self._writePointPenCommand("beginPath", args))

	def endPath(self):
		self.outline.append(self._writePointPenCommand("endPath"))

	def addPoint(self, *args, **kwargs):
		self.outline.append(self._writePointPenCommand("addPoint", args, kwargs))

	def addComponent(self, *args, **kwargs):
		self.outline.append(self._writePointPenCommand("addComponent", args, kwargs))

	def drawPoints(self, pointPen):
		if self.outline:
			py = "\n".join(self.outline)
			exec py in {"pointPen" : pointPen}

	def py(self):
		text = []
		if self.name is not None:
			text.append("glyph.name = \"%s\"" % self.name)
		if self.width:
			text.append("glyph.width = %s" % str(self.width))
		if self.height:
			text.append("glyph.height = %s" % str(self.height))
		if self.unicodes is not None:
			text.append("glyph.unicodes = [%s]" % ", ".join([str(i) for i in self.unicodes]))
		if self.note is not None:
			text.append("glyph.note = \"%s\"" % self.note)
		if self.image is not None:
			text.append("glyph.image = %s" % dictToString(self.image))
		if self.guidelines is not None:
			text.append("glyph.guidelines = %s" % listToString(self.guidelines))
		if self.outline:
			text.append("pointPen = glyph.getPointPen()")
			text += self.outline
		return "\n".join(text)

def dictToString(d):
	text = []
	for key, value in sorted(d.items()):
		if value is None:
			continue
		key = "\"%s\"" % key
		if isinstance(value, dict):
			value = dictToString(value)
		elif isinstance(value, list):
			value = listToString(value)
		elif isinstance(value, tuple):
			value = tupleToString(value)
		elif isinstance(value, (int, float)):
			value = str(value)
		elif isinstance(value, basestring):
			value = "\"%s\"" % value
		text.append("%s : %s" % (key, value))
	return "{%s}" % ", ".join(text)

def listToString(l):
	text = []
	for value in l:
		if isinstance(value, dict):
			value = dictToString(value)
		elif isinstance(value, list):
			value = listToString(value)
		elif isinstance(value, tuple):
			value = tupleToString(value)
		elif isinstance(value, (int, float)):
			value = str(value)
		elif isinstance(value, basestring):
			value = "\"%s\"" % value
		text.append(value)
	return "[%s]" % ", ".join(text)

def tupleToString(t):
	text = []
	for value in t:
		if isinstance(value, dict):
			value = dictToString(value)
		elif isinstance(value, list):
			value = listToString(value)
		elif isinstance(value, tuple):
			value = tupleToString(value)
		elif isinstance(value, (int, float)):
			value = str(value)
		elif isinstance(value, basestring):
			value = "\"%s\"" % value
		text.append(value)
	return "(%s)" % ", ".join(text)


def stripText(text):
	new = []
	for line in text.strip().splitlines():
		line = line.strip()
		if not line:
			continue
		new.append(line)
	return "\n".join(new)

# ----------
# Test Cases
# ----------

class TestGLIF1(unittest.TestCase):

	def assertEqual(self, first, second, msg=None):
		if isinstance(first, basestring):
			first = stripText(first)
		if isinstance(second, basestring):
			second = stripText(second)
		return super(TestGLIF1, self).assertEqual(first, second, msg=msg)

	def glyphToGLIF(self, py):
		py = stripText(py)
		glyph = Glyph()
		exec py in {"glyph" : glyph}
		glif = writeGlyphToString(glyph.name, glyphObject=glyph, drawPointsFunc=glyph.drawPoints, formatVersion=1)
		glif = "\n".join(glif.splitlines()[1:])
		return glif

	def glifToPy(self, glif):
		glif = stripText(glif)
		glif = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + glif
		glyph = Glyph()
		readGlyphFromString(glif, glyphObject=glyph, pointPen=glyph)
		return glyph.py()

	def testTopElement(self):
		# not glyph
		glif = """
		<notglyph name="a" format="1">
			<outline>
			</outline>
		</notglyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testName(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# empty
		glif = """
		<glyph name="" format="1">
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = ""
		"""
		self.assertRaises(GlifLibError, self.glyphToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		# not a string
		py = """
		glyph.name = 1
		"""
		self.assertRaises(GlifLibError, self.glyphToGLIF, py)

	def testFormat(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# wrong number
		glif = """
		<glyph name="a" format="-1">
			<outline>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		# not an int
		glif = """
		<glyph name="a" format="A">
			<outline>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testBogusGlyphStructure(self):
		# unknown element
		glif = """
		<glyph name="a" format="1">
			<unknown />
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		# content
		glif = """
		<glyph name="a" format="1">
			Hello World.
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testAdvance(self):
		# legal: width and height
		glif = """
		<glyph name="a" format="1">
			<advance height="200" width="100"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.width = 100
		glyph.height = 200
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# legal: width and height floats
		glif = """
		<glyph name="a" format="1">
			<advance height="200.1" width="100.1"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.width = 100.1
		glyph.height = 200.1
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# legal: width
		glif = """
		<glyph name="a" format="1">
			<advance width="100"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.width = 100
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# legal: height
		glif = """
		<glyph name="a" format="1">
			<advance height="200"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.height = 200
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# illegal: not a number
		glif = """
		<glyph name="a" format="1">
			<advance width="a"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.width = "a"
		"""
		self.assertRaises(GlifLibError, self.glyphToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		glif = """
		<glyph name="a" format="1">
			<advance height="a"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.height = "a"
		"""
		self.assertRaises(GlifLibError, self.glyphToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testUnicodes(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<unicode hex="0061"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.unicodes = [97]
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		glif = """
		<glyph name="a" format="1">
			<unicode hex="0062"/>
			<unicode hex="0063"/>
			<unicode hex="0061"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.unicodes = [98, 99, 97]
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)
		# illegal
		glif = """
		<glyph name="a" format="1">
			<unicode hex="1.1"/>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "zzzzzz"
		glyph.unicodes = ["1.1"]
		"""
		self.assertRaises(GlifLibError, self.glyphToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testNote(self):
		glif = """
		<glyph name="a" format="1">
			<note>
				hello
			</note>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.note = "hello"
		"""
		resultGlif = self.glyphToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)


if __name__ == "__main__":
	from robofab.test.testSupport import runTests
	runTests()
