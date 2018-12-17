from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals

import os
import shutil
import re
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.misc.psCharStrings import T2CharString


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


def _setupFontBuilder(isTTF, unitsPerEm=1024):
    fb = FontBuilder(unitsPerEm, isTTF=isTTF)
    fb.setupGlyphOrder([".notdef", ".null", "A", "a"])
    fb.setupCharacterMap({65: "A", 97: "a"})

    advanceWidths = {".notdef": 600, "A": 600, "a": 600, ".null": 600}

    familyName = "HelloTestFont"
    styleName = "TotallyNormal"
    nameStrings = dict(familyName=dict(en="HelloTestFont", nl="HalloTestFont"),
                       styleName=dict(en="TotallyNormal", nl="TotaalNormaal"))
    nameStrings['psName'] = familyName + "-" + styleName

    return fb, advanceWidths, nameStrings


def _verifyOutput(outPath):
    f = TTFont(outPath)
    f.saveXML(outPath + ".ttx")
    with open(outPath + ".ttx") as f:
        testData = strip_VariableItems(f.read())
    refData = strip_VariableItems(getTestData(os.path.basename(outPath) + ".ttx"))
    assert refData == testData


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
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    _verifyOutput(outPath)


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
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    _verifyOutput(outPath)


def test_build_var(tmpdir):
    outPath = os.path.join(str(tmpdir), "test_var.ttf")

    fb = FontBuilder(1024, isTTF=True)
    fb.setupGlyphOrder([".notdef", ".null", "A", "a"])
    fb.setupCharacterMap({65: "A", 97: "a"})

    advanceWidths = {".notdef": 600, "A": 600, "a": 600, ".null": 600}

    familyName = "HelloTestFont"
    styleName = "TotallyNormal"
    nameStrings = dict(familyName=dict(en="HelloTestFont", nl="HalloTestFont"),
                       styleName=dict(en="TotallyNormal", nl="TotaalNormaal"))
    nameStrings['psName'] = familyName + "-" + styleName

    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((100, 400))
    pen.lineTo((500, 400))
    pen.lineTo((500, 000))
    pen.closePath()

    glyph = pen.glyph()

    pen = TTGlyphPen(None)
    emptyGlyph = pen.glyph()

    glyphs = {".notdef": emptyGlyph, "A": glyph, "a": glyph, ".null": emptyGlyph}
    fb.setupGlyf(glyphs)
    metrics = {}
    glyphTable = fb.font["glyf"]
    for gn, advanceWidth in advanceWidths.items():
        metrics[gn] = (advanceWidth, glyphTable[gn].xMin)
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupNameTable(nameStrings)

    axes = [
        ('LEFT', 0, 0, 100, "Left"),
        ('RGHT', 0, 0, 100, "Right"),
        ('UPPP', 0, 0, 100, "Up"),
        ('DOWN', 0, 0, 100, "Down"),
    ]
    instances = [
        dict(location=dict(LEFT=0, RGHT=0, UPPP=0, DOWN=0), stylename="TotallyNormal"),
        dict(location=dict(LEFT=0, RGHT=100, UPPP=100, DOWN=0), stylename="Right Up"),
    ]
    fb.setupFvar(axes, instances)
    variations = {}
    # Four (x, y) pairs and four phantom points:
    leftDeltas = [(-200, 0), (-200, 0), (0, 0), (0, 0), None, None, None, None]
    rightDeltas = [(0, 0), (0, 0), (200, 0), (200, 0), None, None, None, None]
    upDeltas = [(0, 0), (0, 200), (0, 200), (0, 0), None, None, None, None]
    downDeltas = [(0, -200), (0, 0), (0, 0), (0, -200), None, None, None, None]
    variations['a'] = [
        TupleVariation(dict(RGHT=(0, 1, 1)), rightDeltas),
        TupleVariation(dict(LEFT=(0, 1, 1)), leftDeltas),
        TupleVariation(dict(UPPP=(0, 1, 1)), upDeltas),
        TupleVariation(dict(DOWN=(0, 1, 1)), downDeltas),
    ]
    fb.setupGvar(variations)

    fb.setupOS2()
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    _verifyOutput(outPath)


def test_build_cff2(tmpdir):
    outPath = os.path.join(str(tmpdir), "test_var.otf")

    fb, advanceWidths, nameStrings = _setupFontBuilder(False, 1000)

    fb.setupNameTable(nameStrings)

    axes = [
        ('TEST', 0, 0, 100, "Test Axis"),
    ]
    instances = [
        dict(location=dict(TEST=0), stylename="TotallyNormal"),
        dict(location=dict(TEST=100), stylename="TotallyTested"),
    ]
    fb.setupFvar(axes, instances)

    pen = T2CharStringPen(None, None, CFF2=True)
    drawTestGlyph(pen)
    charString = pen.getCharString()

    program = [
        200, 200, -200, -200, 2, "blend", "rmoveto",
        400, 400, 1, "blend", "hlineto",
        400, 400, 1, "blend", "vlineto",
        -400, -400, 1, "blend", "hlineto"
    ]
    charStringVariable = T2CharString(program=program)

    charStrings = {".notdef": charString, "A": charString, "a": charStringVariable, ".null": charString}
    fb.setupCFF2(charStrings, regions=[{"TEST": (0, 1, 1)}])

    metrics = {gn: (advanceWidth, 0) for gn, advanceWidth in advanceWidths.items()}
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupOS2(sTypoAscender=825, sTypoDescender=200, usWinAscent=824, usWinDescent=200)
    fb.setupPost()

    fb.save(outPath)

    _verifyOutput(outPath)
