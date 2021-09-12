import logging
import os
import tempfile
import shutil
import unittest
from io import open
from .testSupport import getDemoFontGlyphSetPath
from fontTools.ufoLib.glifLib import (
	GlyphSet, glyphNameToFileName, readGlyphFromString, writeGlyphToString,
)
from fontTools.ufoLib.errors import GlifLibError, UnsupportedGLIFFormat, UnsupportedUFOFormat
from fontTools.misc.etree import XML_DECLARATION
from fontTools.pens.recordingPen import RecordingPointPen
import pytest

GLYPHSETDIR = getDemoFontGlyphSetPath()


class GlyphSetTests(unittest.TestCase):

	def setUp(self):
		self.dstDir = tempfile.mktemp()
		os.mkdir(self.dstDir)

	def tearDown(self):
		shutil.rmtree(self.dstDir)

	def testRoundTrip(self):
		import difflib
		srcDir = GLYPHSETDIR
		dstDir = self.dstDir
		src = GlyphSet(srcDir, ufoFormatVersion=2, validateRead=True, validateWrite=True)
		dst = GlyphSet(dstDir, ufoFormatVersion=2, validateRead=True, validateWrite=True)
		for glyphName in src.keys():
			g = src[glyphName]
			g.drawPoints(None)  # load attrs
			dst.writeGlyph(glyphName, g, g.drawPoints)
		# compare raw file data:
		for glyphName in sorted(src.keys()):
			fileName = src.contents[glyphName]
			with open(os.path.join(srcDir, fileName), "r") as f:
				org = f.read()
			with open(os.path.join(dstDir, fileName), "r") as f:
				new = f.read()
			added = []
			removed = []
			for line in difflib.unified_diff(
					org.split("\n"), new.split("\n")):
				if line.startswith("+ "):
					added.append(line[1:])
				elif line.startswith("- "):
					removed.append(line[1:])
			self.assertEqual(
				added, removed,
				"%s.glif file differs after round tripping" % glyphName)

	def testContentsExist(self):
		with self.assertRaises(GlifLibError):
			GlyphSet(
				self.dstDir,
				ufoFormatVersion=2,
				validateRead=True,
				validateWrite=True,
				expectContentsFile=True,
			)

	def testRebuildContents(self):
		gset = GlyphSet(GLYPHSETDIR, validateRead=True, validateWrite=True)
		contents = gset.contents
		gset.rebuildContents()
		self.assertEqual(contents, gset.contents)

	def testReverseContents(self):
		gset = GlyphSet(GLYPHSETDIR, validateRead=True, validateWrite=True)
		d = {}
		for k, v in gset.getReverseContents().items():
			d[v] = k
		org = {}
		for k, v in gset.contents.items():
			org[k] = v.lower()
		self.assertEqual(d, org)

	def testReverseContents2(self):
		src = GlyphSet(GLYPHSETDIR, validateRead=True, validateWrite=True)
		dst = GlyphSet(self.dstDir, validateRead=True, validateWrite=True)
		dstMap = dst.getReverseContents()
		self.assertEqual(dstMap, {})
		for glyphName in src.keys():
			g = src[glyphName]
			g.drawPoints(None)  # load attrs
			dst.writeGlyph(glyphName, g, g.drawPoints)
		self.assertNotEqual(dstMap, {})
		srcMap = dict(src.getReverseContents())  # copy
		self.assertEqual(dstMap, srcMap)
		del srcMap["a.glif"]
		dst.deleteGlyph("a")
		self.assertEqual(dstMap, srcMap)

	def testCustomFileNamingScheme(self):
		def myGlyphNameToFileName(glyphName, glyphSet):
			return "prefix" + glyphNameToFileName(glyphName, glyphSet)
		src = GlyphSet(GLYPHSETDIR, validateRead=True, validateWrite=True)
		dst = GlyphSet(self.dstDir, myGlyphNameToFileName, validateRead=True, validateWrite=True)
		for glyphName in src.keys():
			g = src[glyphName]
			g.drawPoints(None)  # load attrs
			dst.writeGlyph(glyphName, g, g.drawPoints)
		d = {}
		for k, v in src.contents.items():
			d[k] = "prefix" + v
		self.assertEqual(d, dst.contents)

	def testGetUnicodes(self):
		src = GlyphSet(GLYPHSETDIR, validateRead=True, validateWrite=True)
		unicodes = src.getUnicodes()
		for glyphName in src.keys():
			g = src[glyphName]
			g.drawPoints(None)  # load attrs
			if not hasattr(g, "unicodes"):
				self.assertEqual(unicodes[glyphName], [])
			else:
				self.assertEqual(g.unicodes, unicodes[glyphName])


class FileNameTest:

	def test_default_file_name_scheme(self):
		assert glyphNameToFileName("a", None) == "a.glif"
		assert glyphNameToFileName("A", None) == "A_.glif"
		assert glyphNameToFileName("Aring", None) == "A_ring.glif"
		assert glyphNameToFileName("F_A_B", None) == "F__A__B_.glif"
		assert glyphNameToFileName("A.alt", None) == "A_.alt.glif"
		assert glyphNameToFileName("A.Alt", None) == "A_.A_lt.glif"
		assert glyphNameToFileName(".notdef", None) == "_notdef.glif"
		assert glyphNameToFileName("T_H", None) =="T__H_.glif"
		assert glyphNameToFileName("T_h", None) =="T__h.glif"
		assert glyphNameToFileName("t_h", None) =="t_h.glif"
		assert glyphNameToFileName("F_F_I", None) == "F__F__I_.glif"
		assert glyphNameToFileName("f_f_i", None) == "f_f_i.glif"
		assert glyphNameToFileName("AE", None) == "A_E_.glif"
		assert glyphNameToFileName("Ae", None) == "A_e.glif"
		assert glyphNameToFileName("ae", None) == "ae.glif"
		assert glyphNameToFileName("aE", None) == "aE_.glif"
		assert glyphNameToFileName("a.alt", None) == "a.alt.glif"
		assert glyphNameToFileName("A.aLt", None) == "A_.aL_t.glif"
		assert glyphNameToFileName("A.alT", None) == "A_.alT_.glif"
		assert glyphNameToFileName("Aacute_V.swash", None) == "A_acute_V_.swash.glif"
		assert glyphNameToFileName(".notdef", None) == "_notdef.glif"
		assert glyphNameToFileName("con", None) == "_con.glif"
		assert glyphNameToFileName("CON", None) == "C_O_N_.glif"
		assert glyphNameToFileName("con.alt", None) == "_con.alt.glif"
		assert glyphNameToFileName("alt.con", None) == "alt._con.glif"

	def test_conflicting_case_insensitive_file_names(self, tmp_path):
		src = GlyphSet(GLYPHSETDIR)
		dst = GlyphSet(tmp_path)
		glyph = src["a"]

		dst.writeGlyph("a", glyph)
		dst.writeGlyph("A", glyph)
		dst.writeGlyph("a_", glyph)
		dst.writeGlyph("A_", glyph)
		dst.writeGlyph("i_j", glyph)

		assert dst.contents == {
			'a': 'a.glif',
			'A': 'A_.glif',
			'a_': 'a_000000000000001.glif',
			'A_': 'A__.glif',
			'i_j': 'i_j.glif',
		}

		# make sure filenames are unique even on case-insensitive filesystems
		assert len({fileName.lower() for fileName in dst.contents.values()}) == 5


class _Glyph:
	pass


class ReadWriteFuncTest:

	def test_roundtrip(self):
		glyph = _Glyph()
		glyph.name = "a"
		glyph.unicodes = [0x0061]

		s1 = writeGlyphToString(glyph.name, glyph)

		glyph2 = _Glyph()
		readGlyphFromString(s1, glyph2)
		assert glyph.__dict__ == glyph2.__dict__

		s2 = writeGlyphToString(glyph2.name, glyph2)
		assert s1 == s2

	def test_xml_declaration(self):
		s = writeGlyphToString("a", _Glyph())
		assert s.startswith(XML_DECLARATION % "UTF-8")

	def test_parse_xml_remove_comments(self):
		s = b"""<?xml version='1.0' encoding='UTF-8'?>
		<!-- a comment -->
		<glyph name="A" format="2">
			<advance width="1290"/>
			<unicode hex="0041"/>
			<!-- another comment -->
		</glyph>
		"""

		g = _Glyph()
		readGlyphFromString(s, g)

		assert g.name == "A"
		assert g.width == 1290
		assert g.unicodes == [0x0041]

	def test_read_unsupported_format_version(self, caplog):
		s = """<?xml version='1.0' encoding='utf-8'?>
		<glyph name="A" format="0" formatMinor="0">
			<advance width="500"/>
			<unicode hex="0041"/>
		</glyph>
		"""

		with pytest.raises(UnsupportedGLIFFormat):
			readGlyphFromString(s, _Glyph())  # validate=True by default

		with pytest.raises(UnsupportedGLIFFormat):
			readGlyphFromString(s, _Glyph(), validate=True)

		caplog.clear()
		with caplog.at_level(logging.WARNING, logger="fontTools.ufoLib.glifLib"):
			readGlyphFromString(s, _Glyph(), validate=False)

		assert len(caplog.records) == 1
		assert "Unsupported GLIF format" in caplog.text
		assert "Assuming the latest supported version" in caplog.text

	def test_read_allow_format_versions(self):
		s = """<?xml version='1.0' encoding='utf-8'?>
		<glyph name="A" format="2">
			<advance width="500"/>
			<unicode hex="0041"/>
		</glyph>
		"""

		# these two calls are are equivalent
		readGlyphFromString(s, _Glyph(), formatVersions=[1, 2])
		readGlyphFromString(s, _Glyph(), formatVersions=[(1, 0), (2, 0)])

		# if at least one supported formatVersion, unsupported ones are ignored
		readGlyphFromString(s, _Glyph(), formatVersions=[(2, 0), (123, 456)])

		with pytest.raises(
			ValueError,
			match="None of the requested GLIF formatVersions are supported"
		):
			readGlyphFromString(s, _Glyph(), formatVersions=[0, 2001])

		with pytest.raises(GlifLibError, match="Forbidden GLIF format version"):
			readGlyphFromString(s, _Glyph(), formatVersions=[1])

	def test_read_ensure_x_y(self):
		"""Ensure that a proper GlifLibError is raised when point coordinates are
		missing, regardless of validation setting."""

		s = """<?xml version='1.0' encoding='utf-8'?>
		<glyph name="A" format="2">
			<outline>
				<contour>
					<point x="545" y="0" type="line"/>
					<point x="638" type="line"/>
				</contour>
			</outline>
		</glyph>
		"""
		pen = RecordingPointPen() 

		with pytest.raises(GlifLibError, match="Required y attribute"):
			readGlyphFromString(s, _Glyph(), pen)

		with pytest.raises(GlifLibError, match="Required y attribute"):
			readGlyphFromString(s, _Glyph(), pen, validate=False)

def test_GlyphSet_unsupported_ufoFormatVersion(tmp_path, caplog):
	with pytest.raises(UnsupportedUFOFormat):
		GlyphSet(tmp_path, ufoFormatVersion=0)
	with pytest.raises(UnsupportedUFOFormat):
		GlyphSet(tmp_path, ufoFormatVersion=(0, 1))


def test_GlyphSet_writeGlyph_formatVersion(tmp_path):
	src = GlyphSet(GLYPHSETDIR)
	dst = GlyphSet(tmp_path, ufoFormatVersion=(2, 0))
	glyph = src["A"]

	# no explicit formatVersion passed: use the more recent GLIF formatVersion
	# that is supported by given ufoFormatVersion (GLIF 1 for UFO 2)
	dst.writeGlyph("A", glyph)
	glif = dst.getGLIF("A")
	assert b'format="1"' in glif
	assert b'formatMinor' not in glif  # omitted when 0

	# explicit, unknown formatVersion
	with pytest.raises(UnsupportedGLIFFormat):
		dst.writeGlyph("A", glyph, formatVersion=(0, 0))

	# explicit, known formatVersion but unsupported by given ufoFormatVersion
	with pytest.raises(
		UnsupportedGLIFFormat,
		match="Unsupported GLIF format version .*for UFO format version",
	):
		dst.writeGlyph("A", glyph, formatVersion=(2, 0))
