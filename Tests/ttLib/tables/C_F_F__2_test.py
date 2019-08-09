"""cff2Lib_test.py -- unit test for Adobe CFF fonts."""

from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
import re
import os
import unittest


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, 'data')

CFF_TTX = os.path.join(DATA_DIR, "C_F_F__2.ttx")
CFF_BIN = os.path.join(DATA_DIR, "C_F_F__2.bin")


def strip_VariableItems(string):
    # ttlib changes with the fontTools version
    string = re.sub(' ttLibVersion=".*"', '', string)
    # head table checksum and mod date changes with each save.
    string = re.sub('<checkSumAdjustment value="[^"]+"/>', '', string)
    string = re.sub('<modified value="[^"]+"/>', '', string)
    return string

class CFFTableTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(CFF_BIN, 'rb') as f:
            font = TTFont(file=CFF_BIN)
            cffTable = font['CFF2']
            cls.cff2Data = cffTable.compile(font)
        with open(CFF_TTX, 'r') as f:
            cff2XML = f.read()
            cff2XML = strip_VariableItems(cff2XML)
            cls.cff2XML = cff2XML.splitlines()

    def test_toXML(self):
        font = TTFont(file=CFF_BIN)
        cffTable = font['CFF2']
        cffData = cffTable.compile(font)
        out = UnicodeIO()
        font.saveXML(out)
        cff2XML = out.getvalue()
        cff2XML = strip_VariableItems(cff2XML)
        cff2XML = cff2XML.splitlines()
        self.assertEqual(cff2XML, self.cff2XML)

    def test_fromXML(self):
        font = TTFont(sfntVersion='OTTO')
        font.importXML(CFF_TTX)
        cffTable = font['CFF2']
        cff2Data = cffTable.compile(font)
        self.assertEqual(cff2Data, self.cff2Data)


if __name__ == "__main__":
    unittest.main()
