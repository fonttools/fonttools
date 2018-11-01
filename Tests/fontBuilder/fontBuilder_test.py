from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals

import os
import shutil
import re
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder


def getTestData(fileName, mode="r"):
    path = os.path.join(os.path.dirname(__file__), "data", fileName)
    with open(path, mode) as f:
        return f.read()


def strip_VariableItems(string):
    # ttlib changes with the fontTools version
    string = re.sub(' ttLibVersion=".*"', '', string)
    # head table checksum and creation and mod date changes with each save.
    string = re.sub('<checkSumAdjustment value="[^"]+"/>', '', string)
    string = re.sub('<modified value="[^"]+"/>', '', string)
    string = re.sub('<created value="[^"]+"/>', '', string)
    return string


def drawTestGlyph(pen):
    pen.moveTo((100, 100))
    pen.lineTo((100, 1000))
    pen.qCurveTo((200, 900), (400, 900), (500, 1000))
    pen.lineTo((500, 100))
    pen.closePath()


def _setupFontBuilder(isTTF):
    fb = FontBuilder(1024, isTTF=isTTF)
    fb.setupGlyphOrder([".notdef", ".null", "A", "a"])
    fb.setupCharacterMap({65: "A", 97: "a"})

    advanceWidths = {".notdef": 600, "A": 600, "a": 600, ".null": 600}

    familyName = "HelloTestFont"
    styleName = "TotallyNormal"
    nameStrings = dict(familyName=dict(en="HelloTestFont", nl="HalloTestFont"),
                       styleName=dict(en="TotallyNormal", nl="TotaalNormaal"))
    nameStrings['psName'] = familyName + "-" + styleName

    return fb, advanceWidths, nameStrings


def test_build_ttf(tmpdir):
    outPath = os.path.join(str(tmpdir), "test.ttf")

    fb, advanceWidths, nameStrings = _setupFontBuilder(True)

    pen = TTGlyphPen(None)
    drawTestGlyph(pen)
    glyph = pen.glyph()
    glyphs = {".notdef": glyph, "A": glyph, "a": glyph, ".null": glyph}
    fb.setupGlyf(glyphs)
    metrics = {}
    glyphTable = fb.font["glyf"]
    for gn, advanceWidth in advanceWidths.items():
        metrics[gn] = (advanceWidth, glyphTable[gn].xMin)
    fb.setupMetrics("hmtx", metrics)

    fb.setupHorizontalHeader()
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    f = TTFont(outPath)
    f.saveXML(outPath + ".ttx")
    with open(outPath + ".ttx") as f:
        testData = strip_VariableItems(f.read())
    refData = strip_VariableItems(getTestData("test.ttf.ttx"))
    assert refData == testData


def test_build_otf(tmpdir):
    outPath = os.path.join(str(tmpdir), "test.otf")

    fb, advanceWidths, nameStrings = _setupFontBuilder(False)

    pen = T2CharStringPen(600, None)
    drawTestGlyph(pen)
    charString = pen.getCharString()
    charStrings = {".notdef": charString, "A": charString, "a": charString, ".null": charString}
    fb.setupCFF(nameStrings['psName'], {"FullName": nameStrings['psName']}, charStrings, {})
    metrics = {}
    for gn, advanceWidth in advanceWidths.items():
        metrics[gn] = (advanceWidth, 100)  # XXX lsb from glyph
    fb.setupMetrics("hmtx", metrics)

    fb.setupHorizontalHeader()
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    f = TTFont(outPath)
    f.saveXML(outPath + ".ttx")
    with open(outPath + ".ttx") as f:
        testData = strip_VariableItems(f.read())
    refData = strip_VariableItems(getTestData("test.otf.ttx"))
    assert refData == testData
