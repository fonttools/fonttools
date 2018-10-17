# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import unittest
from fontTools.ufoLib.glifLib import GlifLibError, readGlyphFromString, writeGlyphToString
from .testSupport import Glyph, stripText
from itertools import islice

try:
	basestring
except NameError:
	basestring = str
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

	def pyToGLIF(self, py):
		py = stripText(py)
		glyph = Glyph()
		exec(py, {"glyph" : glyph, "pointPen" : glyph})
		glif = writeGlyphToString(glyph.name, glyphObject=glyph, drawPointsFunc=glyph.drawPoints, formatVersion=1, validate=True)
		# discard the first line containing the xml declaration
		return "\n".join(islice(glif.splitlines(), 1, None))

	def glifToPy(self, glif):
		glif = stripText(glif)
		glif = "<?xml version=\"1.0\"?>\n" + glif
		glyph = Glyph()
		readGlyphFromString(glif, glyphObject=glyph, pointPen=glyph, validate=True)
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

	def testName_legal(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testName_empty(self):
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
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testName_not_a_string(self):
		# not a string
		py = """
		glyph.name = 1
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)

	def testFormat_legal(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testFormat_wrong_number(self):
		# wrong number
		glif = """
		<glyph name="a" format="-1">
			<outline>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testFormat_not_an_int(self):
		# not an int
		glif = """
		<glyph name="a" format="A">
			<outline>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testBogusGlyphStructure_unknown_element(self):
		# unknown element
		glif = """
		<glyph name="a" format="1">
			<unknown />
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testBogusGlyphStructure_content(self):
		# content
		glif = """
		<glyph name="a" format="1">
			Hello World.
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testAdvance_legal_width_and_height(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testAdvance_legal_width_and_height_floats(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testAdvance_legal_width(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testAdvance_legal_height(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testAdvance_illegal_width(self):
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
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testAdvance_illegal_height(self):
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
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testUnicodes_legal(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testUnicodes_legal_multiple(self):
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
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testUnicodes_illegal(self):
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
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testNote(self):
		glif = """
		<glyph name="a" format="1">
			<note>
				\U0001F4A9
			</note>
			<outline>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.note = "💩"
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testLib_legal(self):
		glif = """
		<glyph name="a" format="1">
			<outline>
			</outline>
			<lib>
				<dict>
					<key>dict</key>
					<dict>
						<key>hello</key>
						<string>world</string>
					</dict>
					<key>float</key>
					<real>2.5</real>
					<key>int</key>
					<integer>1</integer>
					<key>list</key>
					<array>
						<string>a</string>
						<string>b</string>
						<integer>1</integer>
						<real>2.5</real>
					</array>
					<key>string</key>
					<string>a</string>
				</dict>
			</lib>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.lib = {"dict" : {"hello" : "world"}, "float" : 2.5, "int" : 1, "list" : ["a", "b", 1, 2.5], "string" : "a"}
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testOutline_unknown_element(self):
		# unknown element
		glif = """
		<glyph name="a" format="1">
			<outline>
				<unknown/>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testOutline_content(self):
		# content
		glif = """
		<glyph name="a" format="1">
			<outline>
				hello
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testComponent_legal(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="2" xyScale="3" yxScale="6" yScale="5" xOffset="1" yOffset="4"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", (2, 3, 6, 5, 1, 4)])
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testComponent_illegal_no_base(self):
		# no base
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component xScale="2" xyScale="3" yxScale="6" yScale="5" xOffset="1" yOffset="4"/>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testComponent_bogus_transformation(self):
		# bogus values in transformation
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="a" xyScale="3" yxScale="6" yScale="5" xOffset="1" yOffset="4"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", ("a", 3, 6, 5, 1, 4)])
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="a" xyScale="3" yxScale="6" yScale="5" xOffset="1" yOffset="4"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", (2, "a", 6, 5, 1, 4)])
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="2" xyScale="3" yxScale="a" yScale="5" xOffset="1" yOffset="4"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", (2, 3, "a", 5, 1, 4)])
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="2" xyScale="3" yxScale="6" yScale="a" xOffset="1" yOffset="4"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", (2, 3, 6, "a", 1, 4)])
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="2" xyScale="3" yxScale="6" yScale="5" xOffset="a" yOffset="4"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", (2, 3, 6, 5, "a", 4)])
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)
		glif = """
		<glyph name="a" format="1">
			<outline>
				<component base="x" xScale="2" xyScale="3" yxScale="6" yScale="5" xOffset="1" yOffset="a"/>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.addComponent(*["x", (2, 3, 6, 5, 1, "a")])
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testContour_legal_one_contour(self):
		# legal: one contour
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testContour_legal_two_contours(self):
		# legal: two contours
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="2" type="move"/>
					<point x="10" y="20" type="line"/>
				</contour>
				<contour>
					<point x="1" y="2" type="move"/>
					<point x="10" y="20" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(10, 20)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		pointPen.beginPath()
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(10, 20)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testContour_illegal_unkonwn_element(self):
		# unknown element
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<unknown/>
				</contour>
			</outline>
		</glyph>
		"""
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointCoordinates_legal_int(self):
		# legal: int
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="-2" type="move"/>
					<point x="0" y="0" type="line" name="this is here so that the contour isn't seen as an anchor"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 0)], **{"name" : "this is here so that the contour isn't seen as an anchor", "segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointCoordinates_legal_float(self):
		# legal: float
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1.1" y="-2.2" type="move"/>
					<point x="0" y="0" type="line" name="this is here so that the contour isn't seen as an anchor"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1.1, -2.2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 0)], **{"name" : "this is here so that the contour isn't seen as an anchor", "segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointCoordinates_illegal_x(self):
		# illegal: string
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="a" y="2" type="move"/>
					<point x="0" y="0" type="line" name="this is here so that the contour isn't seen as an anchor"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[("a", 2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 0)], **{"name" : "this is here so that the contour isn't seen as an anchor", "segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointCoordinates_illegal_y(self):
		# legal: int
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="a" type="move"/>
					<point x="0" y="0" type="line" name="this is here so that the contour isn't seen as an anchor"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, "a")], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 0)], **{"name" : "this is here so that the contour isn't seen as an anchor", "segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointTypeMove_legal(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="-2" type="move"/>
					<point x="3" y="-4" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(3, -4)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeMove_legal_smooth(self):
		# legal: smooth=True
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="-2" type="move" smooth="yes"/>
					<point x="3" y="-4" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "move", "smooth" : True})
		pointPen.addPoint(*[(3, -4)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeMove_illegal_not_at_start(self):
		# illegal: not at start
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="3" y="-4" type="line"/>
					<point x="1" y="-2" type="move"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(3, -4)], **{"segmentType" : "line", "smooth" : False})
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointTypeLine_legal(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="-2" type="move"/>
					<point x="3" y="-4" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(3, -4)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeLine_legal_start_of_contour(self):
		# legal: start of contour
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="-2" type="line"/>
					<point x="3" y="-4" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "line", "smooth" : False})
		pointPen.addPoint(*[(3, -4)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeLine_legal_smooth(self):
		# legal: smooth=True
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="-2" type="move"/>
					<point x="3" y="-4" type="line" smooth="yes"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, -2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(3, -4)], **{"segmentType" : "line", "smooth" : True})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeCurve_legal(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeCurve_legal_start_of_contour(self):
		# legal: start of contour
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="100" y="200" type="curve"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeCurve_legal_smooth(self):
		# legal: smooth=True
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="curve" smooth="yes"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : True})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeCurve_legal_no_off_curves(self):
		# legal: no off-curves
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="100" y="200" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeCurve_legal_1_off_curve(self):
		# legal: 1 off-curve
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="50" y="100"/>
					<point x="100" y="200" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(50, 100)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeCurve_illegal_3_off_curves(self):
		# illegal: 3 off-curves
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="100"/>
					<point x="35" y="125"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 100)], **{"smooth" : False})
		pointPen.addPoint(*[(35, 125)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointQCurve_legal(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="qcurve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "qcurve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointQCurve_legal_start_of_contour(self):
		# legal: start of contour
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="100" y="200" type="qcurve"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "qcurve", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointQCurve_legal_smooth(self):
		# legal: smooth=True
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="qcurve" smooth="yes"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "qcurve", "smooth" : True})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointQCurve_legal_no_off_curves(self):
		# legal: no off-curves
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="100" y="200" type="qcurve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "qcurve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointQCurve_legal_one_off_curve(self):
		# legal: 1 off-curve
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="50" y="100"/>
					<point x="100" y="200" type="qcurve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(50, 100)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "qcurve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointQCurve_legal_3_off_curves(self):
		# legal: 3 off-curves
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="100"/>
					<point x="35" y="125"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="qcurve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 100)], **{"smooth" : False})
		pointPen.addPoint(*[(35, 125)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "qcurve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testSpecialCaseQCurve(self):
		# contour with no on curve
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0"/>
					<point x="0" y="100"/>
					<point x="100" y="100"/>
					<point x="100" y="0"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"smooth" : False})
		pointPen.addPoint(*[(0, 100)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 100)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 0)], **{"smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeOffCurve_legal(self):
		# legal
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="0" type="move"/>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeOffCurve_legal_start_of_contour(self):
		# legal: start of contour
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="65"/>
					<point x="65" y="200"/>
					<point x="100" y="200" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(65, 200)], **{"smooth" : False})
		pointPen.addPoint(*[(100, 200)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testPointTypeOffCurve_illegal_before_move(self):
		# before move
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="65"/>
					<point x="0" y="0" type="move"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "move", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointTypeOffCurve_illegal_before_line(self):
		# before line
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="65"/>
					<point x="0" y="0" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 65)], **{"smooth" : False})
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "line", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testPointTypeOffCurve_illegal_smooth(self):
		# smooth=True
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="0" y="65" smooth="yes"/>
					<point x="0" y="0" type="curve"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(0, 65)], **{"smooth" : True})
		pointPen.addPoint(*[(0, 0)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
		self.assertRaises(GlifLibError, self.glifToPy, glif)

	def testSinglePoint_legal_without_name(self):
		# legal
		# glif format 1 single point without a name was not an anchor
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="2" type="move"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.endPath()
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testAnchor_legal_with_name(self):
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="2" type="move" name="test"/>
				</contour>
			</outline>
		</glyph>
		"""
		py = """
		glyph.name = "a"
		glyph.anchors = [{"name" : "test", "x" : 1, "y" : 2}]
		"""
		resultGlif = self.pyToGLIF(py)
		resultPy = self.glifToPy(glif)
		self.assertEqual(glif, resultGlif)
		self.assertEqual(py, resultPy)

	def testOpenContourLooseOffCurves_legal(self):
		# a piece of software was writing this kind of structure
		glif = """
		<glyph name="a" format="1">
			<outline>
				<contour>
					<point x="1" y="2" type="move"/>
					<point x="1" y="2"/>
					<point x="1" y="2"/>
					<point x="1" y="2" type="curve"/>
					<point x="1" y="2"/>
				</contour>
			</outline>
		</glyph>
		"""
		expectedPy = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.endPath()
		"""
		resultPy = self.glifToPy(glif)
		self.assertEqual(resultPy, expectedPy)

	def testOpenContourLooseOffCurves_illegal(self):
		py = """
		glyph.name = "a"
		pointPen.beginPath()
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "move", "smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"segmentType" : "curve", "smooth" : False})
		pointPen.addPoint(*[(1, 2)], **{"smooth" : False})
		pointPen.endPath()
		"""
		self.assertRaises(GlifLibError, self.pyToGLIF, py)
