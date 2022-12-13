import unittest
import os
import sys
from fontTools import t1Lib
from fontTools.pens.basePen import NullPen
from fontTools.misc.psCharStrings import T1CharString
import random


CWD = os.path.abspath(os.path.dirname(__file__))
DATADIR = os.path.join(CWD, "data")
# I used `tx` to convert PFA to LWFN (stored in the data fork)
LWFN = os.path.join(DATADIR, "TestT1-Regular.lwfn")
PFA = os.path.join(DATADIR, "TestT1-Regular.pfa")
PFB = os.path.join(DATADIR, "TestT1-Regular.pfb")
WEIRD_ZEROS = os.path.join(DATADIR, "TestT1-weird-zeros.pfa")
# ellipsis is hinted with 55 131 296 131 537 131 vstem3 0 122 hstem
ELLIPSIS_HINTED = os.path.join(DATADIR, "TestT1-ellipsis-hinted.pfa")


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
        with open(WEIRD_ZEROS, "rb") as f:
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
        data = self.write(font, "PFB")
        self.assertEqual(font.getData(), data)

    def test_read_and_parse_pfa_write_pfb(self):
        font = t1Lib.T1Font(PFA)
        font.parse()
        saved_font = self.write(font, "PFB", dohex=False, doparse=True)
        self.assertTrue(same_dicts(font.font, saved_font))

    def test_read_pfb_write_pfa(self):
        font = t1Lib.T1Font(PFB)
        # 'OTHER' == 'PFA'
        data = self.write(font, "OTHER", dohex=True)
        self.assertEqual(font.getData(), data)

    def test_read_and_parse_pfb_write_pfa(self):
        font = t1Lib.T1Font(PFB)
        font.parse()
        # 'OTHER' == 'PFA'
        saved_font = self.write(font, "OTHER", dohex=True, doparse=True)
        self.assertTrue(same_dicts(font.font, saved_font))

    def test_read_with_path(self):
        import pathlib

        font = t1Lib.T1Font(pathlib.Path(PFB))

    @staticmethod
    def write(font, outtype, dohex=False, doparse=False):
        temp = os.path.join(DATADIR, "temp." + outtype.lower())
        try:
            font.saveAs(temp, outtype, dohex=dohex)
            newfont = t1Lib.T1Font(temp)
            if doparse:
                newfont.parse()
                data = newfont.font
            else:
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
        self.assertEqual(font["FontName"], "TestT1-Regular")
        self.assertTrue("Subrs" in font["Private"])

    def test_parse_pfa(self):
        font = t1Lib.T1Font(PFA)
        font.parse()
        self.assertEqual(font["FontName"], "TestT1-Regular")
        self.assertTrue("Subrs" in font["Private"])

    def test_parse_pfb(self):
        font = t1Lib.T1Font(PFB)
        font.parse()
        self.assertEqual(font["FontName"], "TestT1-Regular")
        self.assertTrue("Subrs" in font["Private"])

    def test_getGlyphSet(self):
        font = t1Lib.T1Font(PFA)
        glyphs = font.getGlyphSet()
        i = random.randrange(len(glyphs))
        aglyph = list(glyphs.values())[i]
        self.assertTrue(hasattr(aglyph, "draw"))
        self.assertFalse(hasattr(aglyph, "width"))
        aglyph.draw(NullPen())
        self.assertTrue(hasattr(aglyph, "width"))


class EditTest(unittest.TestCase):
    def test_edit_pfa(self):
        font = t1Lib.T1Font(PFA)
        ellipsis = font.getGlyphSet()["ellipsis"]
        ellipsis.decompile()
        program = []
        for v in ellipsis.program:
            try:
                program.append(int(v))
            except:
                program.append(v)
                if v == "hsbw":
                    hints = [55, 131, 296, 131, 537, 131, "vstem3", 0, 122, "hstem"]
                    program.extend(hints)
        ellipsis.program = program
        # 'OTHER' == 'PFA'
        saved_font = self.write(font, "OTHER", dohex=True, doparse=True)
        hinted_font = t1Lib.T1Font(ELLIPSIS_HINTED)
        hinted_font.parse()
        self.assertTrue(same_dicts(hinted_font.font, saved_font))

    @staticmethod
    def write(font, outtype, dohex=False, doparse=False):
        temp = os.path.join(DATADIR, "temp." + outtype.lower())
        try:
            font.saveAs(temp, outtype, dohex=dohex)
            newfont = t1Lib.T1Font(temp)
            if doparse:
                newfont.parse()
                data = newfont.font
            else:
                data = newfont.getData()
        finally:
            if os.path.exists(temp):
                os.remove(temp)
        return data


def same_dicts(dict1, dict2):
    if dict1.keys() != dict2.keys():
        return False
    for key, value in dict1.items():
        if isinstance(value, dict):
            if not same_dicts(value, dict2[key]):
                return False
        elif isinstance(value, list):
            if len(value) != len(dict2[key]):
                return False
            for elem1, elem2 in zip(value, dict2[key]):
                if isinstance(elem1, T1CharString):
                    elem1.compile()
                    elem2.compile()
                    if elem1.bytecode != elem2.bytecode:
                        return False
                else:
                    if elem1 != elem2:
                        return False
        elif isinstance(value, T1CharString):
            value.compile()
            dict2[key].compile()
            if value.bytecode != dict2[key].bytecode:
                return False
        else:
            if value != dict2[key]:
                return False
    return True


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
