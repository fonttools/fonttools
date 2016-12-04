"""C_F_F__2test.py -- unit test for Adobe CFF fonts."""

from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
import os
import unittest
import io

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, 'testdata')

CFF2_TTX = os.path.join(DATA_DIR, "C_F_F__2.ttx")
CFF2_BIN = os.path.join(DATA_DIR, "C_F_F__2.bin")


class CFF2TableTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(CFF2_BIN, 'rb') as f:
            cls.fontData = f.read()
        with open(CFF2_TTX, 'r') as f:
            cls.cffXML = f.read().splitlines()

    def test_toXML(self):
        f = BytesIO(self.fontData)
        font = TTFont(f)
        out = io.StringIO()
        font.saveXML(out)
        cffXML = out.getvalue()
        cffXML= cffXML.splitlines()
        self.assertEqual(cffXML, self.cffXML)

    def test_fromXML(self):
        font = TTFont(sfntVersion='OTTO')
        font.importXML(CFF2_TTX)
        f = BytesIO()
        font.save(f)
        fontData = f.getvalue()
        self.assertEqual(fontData, self.fontData)


if __name__ == "__main__":
    unittest.main()
