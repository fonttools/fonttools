from __future__ import absolute_import, unicode_literals
import os
import tempfile
import shutil
import unittest
from io import open
from .testSupport import getDemoFontGlyphSetPath
from fontTools.ufoLib.glifLib import (
	GlyphSet, glyphNameToFileName, readGlyphFromString, writeGlyphToString,
)
from fontTools.misc.etree import XML_DECLARATION

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


class FileNameTests(unittest.TestCase):

	def testDefaultFileNameScheme(self):
		self.assertEqual(glyphNameToFileName("a", None), "a.glif")
		self.assertEqual(glyphNameToFileName("A", None), "A_.glif")
		self.assertEqual(glyphNameToFileName("Aring", None), "A_ring.glif")
		self.assertEqual(glyphNameToFileName("F_A_B", None), "F__A__B_.glif")
		self.assertEqual(glyphNameToFileName("A.alt", None), "A_.alt.glif")
		self.assertEqual(glyphNameToFileName("A.Alt", None), "A_.A_lt.glif")
		self.assertEqual(glyphNameToFileName(".notdef", None), "_notdef.glif")
		self.assertEqual(glyphNameToFileName("T_H", None), "T__H_.glif")
		self.assertEqual(glyphNameToFileName("T_h", None), "T__h.glif")
		self.assertEqual(glyphNameToFileName("t_h", None), "t_h.glif")
		self.assertEqual(glyphNameToFileName("F_F_I", None), "F__F__I_.glif")
		self.assertEqual(glyphNameToFileName("f_f_i", None), "f_f_i.glif")
		self.assertEqual(glyphNameToFileName("AE", None), "A_E_.glif")
		self.assertEqual(glyphNameToFileName("Ae", None), "A_e.glif")
		self.assertEqual(glyphNameToFileName("ae", None), "ae.glif")
		self.assertEqual(glyphNameToFileName("aE", None), "aE_.glif")
		self.assertEqual(glyphNameToFileName("a.alt", None), "a.alt.glif")
		self.assertEqual(glyphNameToFileName("A.aLt", None), "A_.aL_t.glif")
		self.assertEqual(glyphNameToFileName("A.alT", None), "A_.alT_.glif")
		self.assertEqual(glyphNameToFileName("Aacute_V.swash", None), "A_acute_V_.swash.glif")
		self.assertEqual(glyphNameToFileName(".notdef", None), "_notdef.glif")
		self.assertEqual(glyphNameToFileName("con", None), "_con.glif")
		self.assertEqual(glyphNameToFileName("CON", None), "C_O_N_.glif")
		self.assertEqual(glyphNameToFileName("con.alt", None), "_con.alt.glif")
		self.assertEqual(glyphNameToFileName("alt.con", None), "alt._con.glif")


class _Glyph(object):
	pass


class ReadWriteFuncTest(unittest.TestCase):

	def testRoundTrip(self):
		glyph = _Glyph()
		glyph.name = "a"
		glyph.unicodes = [0x0061]

		s1 = writeGlyphToString(glyph.name, glyph)

		glyph2 = _Glyph()
		readGlyphFromString(s1, glyph2)
		self.assertEqual(glyph.__dict__, glyph2.__dict__)

		s2 = writeGlyphToString(glyph2.name, glyph2)
		self.assertEqual(s1, s2)

	def testXmlDeclaration(self):
		s = writeGlyphToString("a", _Glyph())
		self.assertTrue(s.startswith(XML_DECLARATION % "UTF-8"))
