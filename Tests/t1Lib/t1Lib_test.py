from fontTools.misc.py23 import *
import unittest
import os
import sys
from fontTools import t1Lib
from fontTools.pens.basePen import NullPen
import random


CWD = os.path.abspath(os.path.dirname(__file__))
DATADIR = os.path.join(CWD, 'data')
# I used `tx` to convert PFA to LWFN (stored in the data fork)
LWFN = os.path.join(DATADIR, 'TestT1-Regular.lwfn')
PFA = os.path.join(DATADIR, 'TestT1-Regular.pfa')
PFB = os.path.join(DATADIR, 'TestT1-Regular.pfb')
WEIRD_ZEROS = os.path.join(DATADIR, 'TestT1-weird-zeros.pfa')


class FindEncryptedChunksTest(unittest.TestCase):

	def test_findEncryptedChunks(self):
		with open(PFA, "rb") as f:
			data = f.read()
		chunks = t1Lib.findEncryptedChunks(data)
		self.assertEqual(len(chunks), 3)
		self.assertFalse(chunks[0][0])
		# the second chunk is encrypted
		self.assertTrue(chunks[1][0])
		self.assertFalse(chunks[2][0])

	def test_findEncryptedChunks_weird_zeros(self):
		with open(WEIRD_ZEROS, 'rb') as f:
			data = f.read()

		# Just assert that this doesn't raise any exception for not finding the
		# end of eexec
		t1Lib.findEncryptedChunks(data)


class DecryptType1Test(unittest.TestCase):

	def test_decryptType1(self):
		with open(PFA, "rb") as f:
			data = f.read()
		decrypted = t1Lib.decryptType1(data)
		self.assertNotEqual(decrypted, data)


class ReadWriteTest(unittest.TestCase):

	def test_read_pfa_write_pfb(self):
		font = t1Lib.T1Font(PFA)
		data = self.write(font, 'PFB')
		self.assertEqual(font.getData(), data)

	def test_read_pfb_write_pfa(self):
		font = t1Lib.T1Font(PFB)
		# 'OTHER' == 'PFA'
		data = self.write(font, 'OTHER', dohex=True)
		self.assertEqual(font.getData(), data)

	@unittest.skipIf(sys.version_info[:2] < (3, 6), "pathlib is only tested on 3.6 and up")
	def test_read_with_path(self):
		import pathlib
		font = t1Lib.T1Font(pathlib.Path(PFB))

	@staticmethod
	def write(font, outtype, dohex=False):
		temp = os.path.join(DATADIR, 'temp.' + outtype.lower())
		try:
			font.saveAs(temp, outtype, dohex=dohex)
			newfont = t1Lib.T1Font(temp)
			data = newfont.getData()
		finally:
			if os.path.exists(temp):
				os.remove(temp)
		return data


class T1FontTest(unittest.TestCase):

	def test_parse_lwfn(self):
		# the extended attrs are lost on git so we can't auto-detect 'LWFN'
		font = t1Lib.T1Font(LWFN, kind="LWFN")
		font.parse()
		self.assertEqual(font['FontName'], 'TestT1-Regular')
		self.assertTrue('Subrs' in font['Private'])

	def test_parse_pfa(self):
		font = t1Lib.T1Font(PFA)
		font.parse()
		self.assertEqual(font['FontName'], 'TestT1-Regular')
		self.assertTrue('Subrs' in font['Private'])

	def test_parse_pfb(self):
		font = t1Lib.T1Font(PFB)
		font.parse()
		self.assertEqual(font['FontName'], 'TestT1-Regular')
		self.assertTrue('Subrs' in font['Private'])

	def test_getGlyphSet(self):
		font = t1Lib.T1Font(PFA)
		glyphs = font.getGlyphSet()
		i = random.randrange(len(glyphs))
		aglyph = list(glyphs.values())[i]
		self.assertTrue(hasattr(aglyph, 'draw'))
		self.assertFalse(hasattr(aglyph, 'width'))
		aglyph.draw(NullPen())
		self.assertTrue(hasattr(aglyph, 'width'))


if __name__ == '__main__':
	import sys
	sys.exit(unittest.main())
