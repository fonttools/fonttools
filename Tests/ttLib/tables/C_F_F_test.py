"""cffLib_test.py -- unit test for Adobe CFF fonts."""

from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
import re
import os
import unittest


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, 'data')

CFF_TTX = os.path.join(DATA_DIR, "C_F_F_.ttx")
CFF_BIN = os.path.join(DATA_DIR, "C_F_F_.bin")


def strip_ttLibVersion(string):
    return re.sub(' ttLibVersion=".*"', '', string)


class CFFTableTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(CFF_BIN, 'rb') as f:
            cls.cffData = f.read()
        with open(CFF_TTX, 'r') as f:
            cls.cffXML = strip_ttLibVersion(f.read()).splitlines()

    def test_toXML(self):
        font = TTFont(sfntVersion='OTTO')
        cffTable = font['CFF '] = newTable('CFF ')
        cffTable.decompile(self.cffData, font)
        out = UnicodeIO()
        font.saveXML(out)
        cffXML = strip_ttLibVersion(out.getvalue()).splitlines()
        self.assertEqual(cffXML, self.cffXML)

    def test_fromXML(self):
        font = TTFont(sfntVersion='OTTO')
        font.importXML(CFF_TTX)
        cffTable = font['CFF ']
        cffData = cffTable.compile(font)
        self.assertEqual(cffData, self.cffData)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
