import os
import pytest
from fontTools.designspaceLib import AxisDescriptor
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.misc.psCharStrings import T2CharString
from fontTools.misc.testTools import stripVariableItemsFromTTX


def getTestData(fileName, mode="r"):
    path = os.path.join(os.path.dirname(__file__), "data", fileName)
    with open(path, mode) as f:
        return f.read()


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
    nameStrings = dict(
        familyName=dict(en="HelloTestFont", nl="HalloTestFont"),
        styleName=dict(en="TotallyNormal", nl="TotaalNormaal"),
    )
    nameStrings["psName"] = familyName + "-" + styleName

    return fb, advanceWidths, nameStrings


def _setupFontBuilderFvar(fb):
    assert "name" in fb.font, "Must run setupNameTable() first."

    testAxis = AxisDescriptor()
    testAxis.name = "Test Axis"
    testAxis.tag = "TEST"
    testAxis.minimum = 0
    testAxis.default = 0
    testAxis.maximum = 100
    testAxis.map = [(0, 0), (40, 60), (100, 100)]
    axes = [testAxis]
    instances = [
        dict(location=dict(TEST=0), stylename="TotallyNormal"),
        dict(location=dict(TEST=100), stylename="TotallyTested"),
    ]
    fb.setupFvar(axes, instances)
    fb.setupAvar(axes)

    return fb


def _setupFontBuilderCFF2(fb):
    assert "fvar" in fb.font, "Must run _setupFontBuilderFvar() first."

    pen = T2CharStringPen(None, None, CFF2=True)
    drawTestGlyph(pen)
    charString = pen.getCharString()

    program = [
        200,
        200,
        -200,
        -200,
        2,
        "blend",
        "rmoveto",
        400,
        400,
        1,
        "blend",
        "hlineto",
        400,
        400,
        1,
        "blend",
        "vlineto",
        -400,
        -400,
        1,
        "blend",
        "hlineto",
    ]
    charStringVariable = T2CharString(program=program)

    charStrings = {
        ".notdef": charString,
        "A": charString,
        "a": charStringVariable,
        ".null": charString,
    }
    fb.setupCFF2(charStrings, regions=[{"TEST": (0, 1, 1)}])

    return fb


def _verifyOutput(outPath, tables=None):
    f = TTFont(outPath)
    f.saveXML(outPath + ".ttx", tables=tables)
    with open(outPath + ".ttx") as f:
        testData = stripVariableItemsFromTTX(f.read())
    refData = stripVariableItemsFromTTX(getTestData(os.path.basename(outPath) + ".ttx"))
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
    fb.addOpenTypeFeatures("feature salt { sub A by a; } salt;")
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    _verifyOutput(outPath)


def test_build_cubic_ttf(tmp_path):
    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.curveTo((200, 200), (300, 300), (400, 400))
    pen.closePath()
    glyph = pen.glyph()
    glyphs = {"A": glyph}

    # cubic outlines are not allowed in glyf table format 0
    fb = FontBuilder(1000, isTTF=True, glyphDataFormat=0)
    with pytest.raises(
        ValueError, match="Glyph 'A' has cubic Bezier outlines, but glyphDataFormat=0"
    ):
        fb.setupGlyf(glyphs)
    # can skip check if feeling adventurous
    fb.setupGlyf(glyphs, validateGlyphFormat=False)

    # cubics are (will be) allowed in glyf table format 1
    fb = FontBuilder(1000, isTTF=True, glyphDataFormat=1)
    fb.setupGlyf(glyphs)
    assert "A" in fb.font["glyf"].glyphs


def test_build_otf(tmpdir):
    outPath = os.path.join(str(tmpdir), "test.otf")

    fb, advanceWidths, nameStrings = _setupFontBuilder(False)

    pen = T2CharStringPen(600, None)
    drawTestGlyph(pen)
    charString = pen.getCharString()
    charStrings = {
        ".notdef": charString,
        "A": charString,
        "a": charString,
        ".null": charString,
    }
    fb.setupCFF(
        nameStrings["psName"], {"FullName": nameStrings["psName"]}, charStrings, {}
    )

    lsb = {gn: cs.calcBounds(None)[0] for gn, cs in charStrings.items()}
    metrics = {}
    for gn, advanceWidth in advanceWidths.items():
        metrics[gn] = (advanceWidth, lsb[gn])
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.addOpenTypeFeatures("feature kern { pos A a -50; } kern;")
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    _verifyOutput(outPath)


def test_build_var(tmpdir):
    outPath = os.path.join(str(tmpdir), "test_var.ttf")

    fb, advanceWidths, nameStrings = _setupFontBuilder(True)

    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((100, 400))
    pen.lineTo((500, 400))
    pen.lineTo((500, 000))
    pen.closePath()
    glyph1 = pen.glyph()

    pen = TTGlyphPen(None)
    pen.moveTo((50, 0))
    pen.lineTo((50, 200))
    pen.lineTo((250, 200))
    pen.lineTo((250, 0))
    pen.closePath()
    glyph2 = pen.glyph()

    pen = TTGlyphPen(None)
    emptyGlyph = pen.glyph()

    glyphs = {".notdef": emptyGlyph, "A": glyph1, "a": glyph2, ".null": emptyGlyph}
    fb.setupGlyf(glyphs)
    metrics = {}
    glyphTable = fb.font["glyf"]
    for gn, advanceWidth in advanceWidths.items():
        metrics[gn] = (advanceWidth, glyphTable[gn].xMin)
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupNameTable(nameStrings)

    axes = [
        ("LEFT", 0, 0, 100, "Left"),
        ("RGHT", 0, 0, 100, "Right"),
        ("UPPP", 0, 0, 100, "Up"),
        ("DOWN", 0, 0, 100, "Down"),
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
    variations["a"] = [
        TupleVariation(dict(RGHT=(0, 1, 1)), rightDeltas),
        TupleVariation(dict(LEFT=(0, 1, 1)), leftDeltas),
        TupleVariation(dict(UPPP=(0, 1, 1)), upDeltas),
        TupleVariation(dict(DOWN=(0, 1, 1)), downDeltas),
    ]
    fb.setupGvar(variations)

    fb.addFeatureVariations(
        [
            (
                [
                    {"LEFT": (0.8, 1), "DOWN": (0.8, 1)},
                    {"RGHT": (0.8, 1), "UPPP": (0.8, 1)},
                ],
                {"A": "a"},
            )
        ],
        featureTag="rclt",
    )

    statAxes = []
    for tag, minVal, defaultVal, maxVal, name in axes:
        values = [
            dict(name="Neutral", value=defaultVal, flags=0x2),
            dict(name=name, value=maxVal),
        ]
        statAxes.append(dict(tag=tag, name=name, values=values))
    fb.setupStat(statAxes)

    fb.setupOS2()
    fb.setupPost()
    fb.setupDummyDSIG()

    fb.save(outPath)

    _verifyOutput(outPath)


def test_build_cff2(tmpdir):
    outPath = os.path.join(str(tmpdir), "test_var.otf")

    fb, advanceWidths, nameStrings = _setupFontBuilder(False, 1000)
    fb.setupNameTable(nameStrings)
    fb = _setupFontBuilderFvar(fb)
    fb = _setupFontBuilderCFF2(fb)

    metrics = {gn: (advanceWidth, 0) for gn, advanceWidth in advanceWidths.items()}
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupOS2(
        sTypoAscender=825, sTypoDescender=200, usWinAscent=824, usWinDescent=200
    )
    fb.setupPost()

    fb.save(outPath)

    _verifyOutput(outPath)


def test_build_cff_to_cff2(tmpdir):
    fb, _, _ = _setupFontBuilder(False, 1000)

    pen = T2CharStringPen(600, None)
    drawTestGlyph(pen)
    charString = pen.getCharString()
    charStrings = {
        ".notdef": charString,
        "A": charString,
        "a": charString,
        ".null": charString,
    }
    fb.setupCFF("TestFont", {}, charStrings, {})

    from fontTools.varLib.cff import convertCFFtoCFF2

    convertCFFtoCFF2(fb.font)


def test_setupNameTable_no_mac():
    fb, _, nameStrings = _setupFontBuilder(True)
    fb.setupNameTable(nameStrings, mac=False)

    assert all(n for n in fb.font["name"].names if n.platformID == 3)
    assert not any(n for n in fb.font["name"].names if n.platformID == 1)


def test_setupNameTable_no_windows():
    fb, _, nameStrings = _setupFontBuilder(True)
    fb.setupNameTable(nameStrings, windows=False)

    assert all(n for n in fb.font["name"].names if n.platformID == 1)
    assert not any(n for n in fb.font["name"].names if n.platformID == 3)


@pytest.mark.parametrize(
    "is_ttf, keep_glyph_names, make_cff2, post_format",
    [
        (True, True, False, 2),  # TTF with post table format 2.0
        (True, False, False, 3),  # TTF with post table format 3.0
        (False, True, False, 3),  # CFF with post table format 3.0
        (False, False, False, 3),  # CFF with post table format 3.0
        (False, True, True, 2),  # CFF2 with post table format 2.0
        (False, False, True, 3),  # CFF2 with post table format 3.0
    ],
)
def test_setupPost(is_ttf, keep_glyph_names, make_cff2, post_format):
    fb, _, nameStrings = _setupFontBuilder(is_ttf)

    if make_cff2:
        fb.setupNameTable(nameStrings)
        fb = _setupFontBuilderCFF2(_setupFontBuilderFvar(fb))

    if keep_glyph_names:
        fb.setupPost()
    else:
        fb.setupPost(keepGlyphNames=keep_glyph_names)

    assert fb.isTTF is is_ttf
    assert ("CFF2" in fb.font) is make_cff2
    assert fb.font["post"].formatType == post_format


def test_unicodeVariationSequences(tmpdir):
    familyName = "UVSTestFont"
    styleName = "Regular"
    nameStrings = dict(familyName=familyName, styleName=styleName)
    nameStrings["psName"] = familyName + "-" + styleName
    glyphOrder = [".notdef", "space", "zero", "zero.slash"]
    cmap = {ord(" "): "space", ord("0"): "zero"}
    uvs = [
        (0x0030, 0xFE00, "zero.slash"),
        (0x0030, 0xFE01, None),  # not an official sequence, just testing
    ]
    metrics = {gn: (600, 0) for gn in glyphOrder}
    pen = TTGlyphPen(None)
    glyph = pen.glyph()  # empty placeholder
    glyphs = {gn: glyph for gn in glyphOrder}

    fb = FontBuilder(1024, isTTF=True)
    fb.setupGlyphOrder(glyphOrder)
    fb.setupCharacterMap(cmap, uvs)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=824, descent=200)
    fb.setupNameTable(nameStrings)
    fb.setupOS2()
    fb.setupPost()

    outPath = os.path.join(str(tmpdir), "test_uvs.ttf")
    fb.save(outPath)
    _verifyOutput(outPath, tables=["cmap"])

    uvs = [
        (0x0030, 0xFE00, "zero.slash"),
        (
            0x0030,
            0xFE01,
            "zero",
        ),  # should result in the exact same subtable data, due to cmap[0x0030] == "zero"
    ]
    fb.setupCharacterMap(cmap, uvs)
    fb.save(outPath)
    _verifyOutput(outPath, tables=["cmap"])


def test_setupPanose():
    from fontTools.ttLib.tables.O_S_2f_2 import Panose

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

    panoseValues = {  # sample value of Times New Roman from https://www.w3.org/Printing/stevahn.html
        "bFamilyType": 2,
        "bSerifStyle": 2,
        "bWeight": 6,
        "bProportion": 3,
        "bContrast": 5,
        "bStrokeVariation": 4,
        "bArmStyle": 5,
        "bLetterForm": 2,
        "bMidline": 3,
        "bXHeight": 4,
    }
    panoseObj = Panose(**panoseValues)

    for name in panoseValues:
        assert getattr(fb.font["OS/2"].panose, name) == 0

    fb.setupOS2(panose=panoseObj)
    fb.setupPost()

    for name, value in panoseValues.items():
        assert getattr(fb.font["OS/2"].panose, name) == value
