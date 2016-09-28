"""cffLib_test.py -- unit test for Adobe CFF fonts."""

from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTFont, newTable
import re
import unittest


cffXML = """
<major value="1"/>
<minor value="0"/>
<CFFFont name="CFF2TestFont1Master-0">
  <version value="1.0"/>
  <FullName value="CFF2 Test Font1 Master 0"/>
  <FamilyName value="CFF2 Test Font1 Master"/>
  <isFixedPitch value="0"/>
  <ItalicAngle value="0"/>
  <UnderlineThickness value="50"/>
  <PaintType value="0"/>
  <CharstringType value="2"/>
  <FontMatrix value="0.001 0 0 0.001 0 0"/>
  <FontBBox value="0 -128 651 762"/>
  <StrokeWidth value="0"/>
  <!-- charset is dumped separately as the 'GlyphOrder' element -->
  <Encoding name="StandardEncoding"/>
  <Private>
    <BlueValues value="-20 0 466 484 531 546 652 667 677 697 738 758"/>
    <OtherBlues value="-255 -245"/>
    <FamilyBlues value="-20 0 473 491 525 540 644 659 669 689 729 749"/>
    <FamilyOtherBlues value="-249 -239"/>
    <BlueScale value="0.0375"/>
    <BlueShift value="7"/>
    <BlueFuzz value="0"/>
    <StdHW value="26"/>
    <StdVW value="28"/>
    <StemSnapH value="20 26"/>
    <StemSnapV value="28 32"/>
    <ForceBold value="0"/>
    <LanguageGroup value="0"/>
    <ExpansionFactor value="0.06"/>
    <initialRandomSeed value="0"/>
    <defaultWidthX value="490"/>
    <nominalWidthX value="597"/>
  </Private>
  <CharStrings>
    <CharString name=".notdef">
      -97 0 50 600 50 hstem
      0 50 400 50 vstem
      0 0 rmoveto
      500 0 rlineto
      0 700 rlineto
      -500 0 rlineto
      0 -700 rlineto
      250 395 rmoveto
      -170 255 rlineto
      340 0 rlineto
      -170 -255 rlineto
      30 -45 rmoveto
      170 255 rlineto
      0 -510 rlineto
      -170 255 rlineto
      -200 -300 rmoveto
      170 255 rlineto
      170 -255 rlineto
      -340 0 rlineto
      -30 555 rmoveto
      170 -255 rlineto
      -170 -255 rlineto
      0 510 rlineto
      endchar
    </CharString>
    <CharString name="A">
      56 523 26 rmoveto
      -120 -6 rlineto
      0 -20 rlineto
      248 0 rlineto
      0 20 rlineto
      -114 6 rlineto
      -14 0 rlineto
      -424 0 rmoveto
      -87 -6 rlineto
      0 -20 rlineto
      198 0 rlineto
      0 20 rlineto
      -97 6 rlineto
      -14 0 rlineto
      369 221 rmoveto
      -8 20 rlineto
      -278 0 rlineto
      -9 -20 rlineto
      295 0 rlineto
      -161 430 rmoveto
      -222 -677 rlineto
      27 0 rlineto
      211 660 rlineto
      -17 -10 rlineto
      216 -650 rlineto
      34 0 rlineto
      -229 677 rlineto
      -20 0 rlineto
      endchar
    </CharString>
    <CharString name="B">
      -3 167 310 rmoveto
      0 -104 0 -104 -2 -102 rrcurveto
      34 0 rlineto
      -2 102 0 104 0 144 rrcurveto
      0 7 rlineto
      0 114 0 104 2 102 rrcurveto
      -34 0 rlineto
      2 -102 0 -104 0 -104 rrcurveto
      0 -57 rlineto
      8 340 rmoveto
      7 0 rlineto
      0 27 rlineto
      -124 0 rlineto
      0 -20 rlineto
      117 -7 rlineto
      0 -623 rmoveto
      -117 -7 rlineto
      0 -20 rlineto
      124 0 rlineto
      0 27 rlineto
      -7 0 rlineto
      7 316 rmoveto
      101 0 rlineto
      162 0 69 -60 0 -102 rrcurveto
      0 -102 -75 -57 -125 0 rrcurveto
      -132 0 rlineto
      0 -22 rlineto
      131 0 rlineto
      156 0 75 77 0 102 rrcurveto
      0 100 -68 76 -162 2 rrcurveto
      -10 -8 rlineto
      141 11 64 75 0 84 rrcurveto
      0 95 -66 63 -146 0 rrcurveto
      -115 0 rlineto
      0 -22 rlineto
      104 0 rlineto
      145 0 50 -57 0 -76 rrcurveto
      0 -95 -75 -64 -136 0 rrcurveto
      -88 0 rlineto
      0 -20 rlineto
      endchar
    </CharString>
    <CharString name="C">
      47 386 7 rmoveto
      -167 0 -123 128 0 203 rrcurveto
      0 199 116 133 180 0 rrcurveto
      73 0 40 -17 56 -37 rrcurveto
      -21 29 rlineto
      18 -145 rlineto
      24 0 rlineto
      -4 139 rlineto
      -60 35 -49 18 -80 0 rrcurveto
      -190 0 -135 -144 0 -210 rrcurveto
      0 -209 129 -144 195 0 rrcurveto
      72 0 57 12 67 41 rrcurveto
      4 139 rlineto
      -24 0 rlineto
      -18 -139 rlineto
      17 20 rlineto
      -55 -37 -55 -14 -67 0 rrcurveto
      endchar
    </CharString>
    <CharString name="dollar">
      245 5 rmoveto
      -65 0 -39 15 -46 50 rrcurveto
      36 -48 rlineto
      -28 100 rlineto
      -6 15 -10 5 -11 0 rrcurveto
      -14 0 -8 -7 -1 -14 rrcurveto
      24 -85 61 -51 107 0 rrcurveto
      91 0 90 54 0 112 rrcurveto
      0 70 -26 66 -134 57 rrcurveto
      -19 8 rlineto
      -93 39 -42 49 0 68 rrcurveto
      0 91 60 48 88 0 rrcurveto
      56 0 35 -14 44 -50 rrcurveto
      -38 47 rlineto
      28 -100 rlineto
      6 -15 10 -5 11 0 rrcurveto
      14 0 8 7 1 14 rrcurveto
      -24 88 -67 48 -84 0 rrcurveto
      -92 0 -82 -51 0 -108 rrcurveto
      0 -80 45 -53 92 -42 rrcurveto
      37 -17 rlineto
      114 -52 26 -46 0 -65 rrcurveto
      0 -93 -65 -55 -90 0 rrcurveto
      18 318 rmoveto
      0 439 rlineto
      -22 0 rlineto
      0 -425 rlineto
      22 -14 rlineto
      -20 -438 rmoveto
      22 0 rlineto
      0 438 rlineto
      -22 14 rlineto
      0 -452 rlineto
      endchar
    </CharString>
    <CharString name="dollar.black">
      3 245 5 rmoveto
      -65 0 -39 15 -46 50 rrcurveto
      36 -48 rlineto
      -28 100 rlineto
      -6 15 -10 5 -11 0 rrcurveto
      -14 0 -8 -7 -1 -14 rrcurveto
      24 -85 61 -51 107 0 rrcurveto
      91 0 90 54 0 112 rrcurveto
      0 70 -26 66 -134 57 rrcurveto
      -19 8 rlineto
      -93 39 -42 49 0 68 rrcurveto
      0 91 60 48 88 0 rrcurveto
      56 0 35 -14 44 -50 rrcurveto
      -38 47 rlineto
      28 -100 rlineto
      6 -15 10 -5 11 0 rrcurveto
      14 0 8 7 1 14 rrcurveto
      -24 88 -67 48 -84 0 rrcurveto
      -92 0 -82 -51 0 -108 rrcurveto
      0 -80 45 -53 92 -42 rrcurveto
      37 -17 rlineto
      114 -52 26 -46 0 -65 rrcurveto
      0 -93 -65 -55 -90 0 rrcurveto
      17 651 rmoveto
      1 106 rlineto
      -22 0 rlineto
      1 -107 rlineto
      20 1 rlineto
      -15 -784 rmoveto
      22 0 rlineto
      -3 121 rlineto
      -20 2 rlineto
      1 -123 rlineto
      endchar
    </CharString>
    <CharString name="one">
      91 618 rmoveto
      0 -20 rlineto
      155 35 rlineto
      0 -421 rlineto
      0 -70 -1 -71 -2 -72 rrcurveto
      34 0 rlineto
      -2 72 -1 71 0 70 rrcurveto
      0 297 rlineto
      4 146 rlineto
      -14 12 rlineto
      -173 -49 rlineto
      176 -593 rmoveto
      -14 0 rlineto
      -170 -6 rlineto
      0 -20 rlineto
      344 0 rlineto
      0 20 rlineto
      -160 6 rlineto
      endchar
    </CharString>
    <CharString name="three">
      endchar
    </CharString>
    <CharString name="two">
      endchar
    </CharString>
  </CharStrings>
</CFFFont>

<GlobalSubrs>
  <!-- The 'index' attribute is only for humans; it is ignored when parsed. -->
</GlobalSubrs>
"""

cffHexData = """
01 00 04 02 00 01 01 01 16 43 46 46 32 54 65 73 74 46 6F 6E 74 31 4D 61 73 74
65 72 2D 30 00 01 01 01 1C F8 1C 00 F8 1D 02 F8 1E 03 8B FB 14 F9 1F F9 8E 05 F7
19 0F CA FA E4 12 F7 26 11 00 04 01 01 0D 10 28 3E 64 6F 6C 6C 61 72 2E 62 6C 61
63 6B 31 2E 30 43 46 46 32 20 54 65 73 74 20 46 6F 6E 74 31 20 4D 61 73 74 65 72
20 30 43 46 46 32 20 54 65 73 74 20 46 6F 6E 74 31 20 4D 61 73 74 65 72 00 00 01
00 05 00 00 12 02 00 22 02 01 87 00 00 09 02 00 01 00 6B 01 1A 01 64 01 65 01 66
01 D0 02 90 02 FA 03 A8 2A 8B BD F8 EC BD 01 8B BD F8 24 BD 03 8B 8B 15 F8 88 8B
05 8B F9 50 05 FC 88 8B 05 8B FD 50 05 F7 8E F8 1F 15 FB 3E F7 93 05 F7 E8 8B 05
FB 3E FB 93 05 A9 5E 15 F7 3E F7 93 05 8B FC 92 05 FB 3E F7 93 05 FB 5C FB C0 15
F7 3E F7 93 05 F7 3E FB 93 05 FB E8 8B 05 6D F8 BF 15 F7 3E FB 93 05 FB 3E FB 93
05 8B F8 92 05 0E F7 89 90 15 4A 8B 64 9A 5D BD 08 AF 5B 05 6F EF 05 85 9A 81 90
80 8B 08 7D 8B 83 84 8A 7D 08 A3 36 C8 58 F6 8B 08 E6 8B E5 C1 8B F7 04 08 8B D1
71 CD FB 1A C4 08 78 93 05 2E B2 61 BC 8B CF 08 8B E6 C7 BB E3 8B 08 C3 8B AE 7D
B7 59 08 65 BA 05 A7 27 05 91 7C 95 86 96 8B 08 99 8B 93 92 8C 99 08 73 E3 48 BB
37 8B 08 2F 8B 39 58 8B FB 00 08 8B 3B B8 56 E7 61 08 B0 7A 05 F7 06 57 A5 5D 8B
4A 08 8B 2E 4A 54 31 8B 08 9D F7 D2 15 8B F8 4B 05 75 8B 05 8B FC 3D 05 A1 7D 05
77 FC 4A 15 A1 8B 05 8B F8 4A 05 75 99 05 8B FC 58 05 0E E6 F8 FE 15 8B 77 05 F7
2F AE 05 8B FC 39 05 8B 45 8A 44 89 43 08 AD 8B 05 89 D3 8A D2 8B D1 08 8B F7 BD
05 8F F7 26 05 7D 97 05 FB 41 5A 05 F7 44 FC E5 15 7D 8B 05 FB 3E 85 05 8B 77 05
F7 EC 8B 05 8B 9F 05 FB 34 91 05 0E 0E 0E C3 F8 9F A5 15 FB 0C 85 05 8B 77 05 F7
8C 8B 05 8B 9F 05 FB 06 91 05 7D 8B 05 FC 3C 8B 15 34 85 05 8B 77 05 F7 5A 8B 05
8B 9F 05 2A 91 05 7D 8B 05 F8 05 F7 71 15 83 9F 05 FB AA 8B 05 82 77 05 F7 BB 8B
05 FB 35 F8 42 15 FB 72 FD 39 05 A6 8B 05 F7 67 F9 28 05 7A 81 05 F7 6C FD 1E 05
AD 8B 05 FB 79 F9 39 05 77 8B 05 0E 88 F7 3B F7 CA 15 8B 23 8B 23 89 25 08 AD 8B
05 89 F1 8B F3 8B F7 24 08 8B 92 05 8B F7 06 8B F3 8D F1 08 69 8B 05 8D 25 8B 23
8B 23 08 8B 52 05 93 F7 E8 15 92 8B 05 8B A6 05 FB 10 8B 05 8B 77 05 F7 09 84 05
8B FD 03 15 FB 09 84 05 8B 77 05 F7 10 8B 05 8B A6 05 84 8B 05 92 F7 D0 15 F0 8B
05 F7 36 8B D0 4F 8B 25 08 8B 25 40 52 FB 11 8B 08 FB 18 8B 05 8B 75 05 F7 17 8B
05 F7 30 8B D6 D8 8B F1 08 8B EF 47 D7 FB 36 8D 08 81 83 05 F7 21 96 CB D6 8B DF
08 8B EA 49 CA FB 26 8B 08 FB 07 8B 05 8B 75 05 F3 8B 05 F7 25 8B BD 52 8B 3F 08
8B 2C 40 4B FB 1C 8B 08 33 8B 05 8B 77 05 0E BA F8 16 92 15 FB 3B 8B FB 0F F7 14
8B F7 5F 08 8B F7 5B F7 08 F7 19 F7 48 8B 08 D4 8B B3 7A C3 66 08 76 A8 05 9D FB
25 05 A3 8B 05 87 F7 1F 05 4F AE 5A 9D 3B 8B 08 FB 52 8B FB 1B FB 24 8B FB 66 08
8B FB 65 F7 15 FB 24 F7 57 8B 08 D3 8B C4 97 CE B4 08 8F F7 1F 05 73 8B 05 79 FB
1F 05 9C 9F 05 54 66 54 7D 48 8B 08 0E 8E F7 89 90 15 4A 8B 64 9A 5D BD 08 AF 5B
05 6F EF 05 85 9A 81 90 80 8B 08 7D 8B 83 84 8A 7D 08 A3 36 C8 58 F6 8B 08 E6 8B
E5 C1 8B F7 04 08 8B D1 71 CD FB 1A C4 08 78 93 05 2E B2 61 BC 8B CF 08 8B E6 C7
BB E3 8B 08 C3 8B AE 7D B7 59 08 65 BA 05 A7 27 05 91 7C 95 86 96 8B 08 99 8B 93
92 8C 99 08 73 E3 48 BB 37 8B 08 2F 8B 39 58 8B FB 00 08 8B 3B B8 56 E7 61 08 B0
7A 05 F7 06 57 A5 5D 8B 4A 08 8B 2E 4A 54 31 8B 08 9C F9 1F 15 8C F5 05 75 8B 05
8C 20 05 9F 8C 05 7C FD A4 15 A1 8B 05 88 F7 0D 05 77 8D 05 8C FB 0F 05 0E 77 9F
F8 66 9D BA 9A F5 9A 95 9F B4 9F 06 FB 93 95 07 77 9F F8 6D 9D AD 9A F3 9A 95 9F
B3 9F 08 FB 8D 95 09 1E A0 37 5F 0C 09 8B 0C 0B A5 0A A7 0B 9F 91 0C 0C A7 8F 0C
0D F8 7E 14 F8 E9 15"""

glyphOrder = ['.notdef', 'dollar', 'one', 'two', 'three', 'A', 'B', 'C', 'dollar.black']

def hexencode(s):
    h = hexStr(s).upper()
    return ' '.join([h[i:i+2] for i in range(0, len(h), 2)])

def parseTableXML(otTable, xmlText, font):
    xmlList = parseXML(xmlText)
    for entry in xmlList:
        if len(entry) != 3: # skip comments and newlines.
            continue
        name, attrs, content = entry
        otTable.fromXML(name, attrs, content, font)

def MakeFont():
        font = TTFont()
        return font

class CFFTableTest(unittest.TestCase):
    def test_toXML(self):
        global cffXML
        # make font with post table.
        font = MakeFont()

        cffData = deHexStr(cffHexData)
        CFF2Table = font['CFF '] = newTable('CFF ')
        CFF2Table.decompile(cffData, font)
        writer = XMLWriter(UnicodeIO())
        font['CFF '].toXML(writer, font)
        xml = writer.file.getvalue()
        # normalize spacing and new-lines, so we can edit the XML without being very careful.
        # cffXML does not have the initial xml definition line.
        xml = re.sub(r"\<\?xml[^\r\n]+", "", xml)
        self.assertEqual(xml, cffXML)

    def test_fromXML(self):
        global cffHexData
        from fontTools.misc import xmlReader
        font = MakeFont()
        # charset data is stored in the ttx GlyphOrder table, not
        # in the CFF XML dump. Need to to provide this externally to the
        # ttx dump of the CFF table.
        font.glyphOrder = glyphOrder
        cffTable = font['CFF '] = newTable('CFF ')
        cffXML2 = cffXML
        parseTableXML(cffTable, cffXML, font)
        cffData = cffTable.compile(font)
        cffHexDatafromTable = hexencode(cffData)
        cffHexDatafromTable = re.sub(r"\s+", " ", cffHexDatafromTable)
        cffHexDatafromTable = cffHexDatafromTable.strip()
        cffHexData = re.sub(r"\s+", " ", cffHexData)
        cffHexData = cffHexData.strip()
        self.assertEqual(cffHexDatafromTable, cffHexData)


if __name__ == "__main__":
    unittest.main()
