from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals

__all__ = ["FontBuilder"]

"""
This module is *experimental*, meaning it still may evolve and change.

The `FontBuilder` class is a convenient helper to construct working TTF or
OTF fonts from scratch.

Note that the various setup methods cannot be called in arbitrary order,
due to various interdependencies between OpenType tables. Here is an order
that works:

    fb = FontBuilder(...)
    fb.setupGlyphOrder(...)
    fb.setupCharacterMap(...)
    fb.setupGlyf(...) --or-- fb.setupCFF(...)
    fb.setupMetrics("hmtx", ...)
    fb.setupHorizontalHeader()
    fb.setupNameTable(...)
    fb.setupOS2()
    fb.setupPost()
    fb.save(...)

Here is how to build a minimal TTF:

```python
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

def drawTestGlyph(pen):
    pen.moveTo((100, 100))
    pen.lineTo((100, 1000))
    pen.qCurveTo((200, 900), (400, 900), (500, 1000))
    pen.lineTo((500, 100))
    pen.closePath()

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

fb.save("test.ttf")
```

And here's how to build a minimal OTF:

```python
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen

def drawTestGlyph(pen):
    pen.moveTo((100, 100))
    pen.lineTo((100, 1000))
    pen.curveTo((200, 900), (400, 900), (500, 1000))
    pen.lineTo((500, 100))
    pen.closePath()

fb = FontBuilder(1024, isTTF=False)
fb.setupGlyphOrder([".notdef", ".null", "A", "a"])
fb.setupCharacterMap({65: "A", 97: "a"})

advanceWidths = {".notdef": 600, "A": 600, "a": 600, ".null": 600}

familyName = "HelloTestFont"
styleName = "TotallyNormal"
nameStrings = dict(familyName=dict(en="HelloTestFont", nl="HalloTestFont"),
                   styleName=dict(en="TotallyNormal", nl="TotaalNormaal"))
nameStrings['psName'] = familyName + "-" + styleName

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

fb.save("test.otf")
```
"""

from .misc.py23 import *
from .ttLib import TTFont, newTable
from .ttLib.tables._c_m_a_p import cmap_classes
from .ttLib.tables._n_a_m_e import NameRecord, makeName
from .misc.timeTools import timestampNow
import struct


_headDefaults = dict(
    tableVersion = 1.0,
    fontRevision = 1.0,
    checkSumAdjustment = 0,
    magicNumber = 0x5F0F3CF5,
    flags = 0x0003,
    unitsPerEm = 1000,
    created = 0,
    modified = 0,
    xMin = 0,
    yMin = 0,
    xMax = 0,
    yMax = 0,
    macStyle = 0,
    lowestRecPPEM = 3,
    fontDirectionHint = 2,
    indexToLocFormat = 0,
    glyphDataFormat = 0,
)

_maxpDefaultsTTF = dict(
    tableVersion = 0x00010000,
    numGlyphs = 0,
    maxPoints = 0,
    maxContours = 0,
    maxCompositePoints = 0,
    maxCompositeContours = 0,
    maxZones = 2,
    maxTwilightPoints = 0,
    maxStorage = 0,
    maxFunctionDefs = 0,
    maxInstructionDefs = 0,
    maxStackElements = 0,
    maxSizeOfInstructions = 0,
    maxComponentElements = 0,
    maxComponentDepth = 0,
)
_maxpDefaultsOTF = dict(
    tableVersion = 0x00005000,
    numGlyphs = 0,
)

_postDefaults = dict(
    formatType = 3.0,
    italicAngle = 0,
    underlinePosition = 0,
    underlineThickness = 0,
    isFixedPitch = 0,
    minMemType42 = 0,
    maxMemType42 = 0,
    minMemType1 = 0,
    maxMemType1 = 0,
)

_hheaDefaults = dict(
    tableVersion = 0x00010000,
    ascent = 0,
    descent = 0,
    lineGap = 0,
    advanceWidthMax = 0,
    minLeftSideBearing = 0,
    minRightSideBearing = 0,
    xMaxExtent = 0,
    caretSlopeRise = 1,
    caretSlopeRun = 0,
    caretOffset = 0,
    reserved0 = 0,
    reserved1 = 0,
    reserved2 = 0,
    reserved3 = 0,
    metricDataFormat = 0,
    numberOfHMetrics = 0,
)

_vheaDefaults = dict(
    tableVersion = 0x00010000,
    ascent = 0,
    descent = 0,
    lineGap = 0,
    advanceHeightMax = 0,
    minTopSideBearing = 0,
    minBottomSideBearing = 0,
    yMaxExtent = 0,
    caretSlopeRise = 0,
    caretSlopeRun = 0,
    reserved0 = 0,
    reserved1 = 0,
    reserved2 = 0,
    reserved3 = 0,
    reserved4 = 0,
    metricDataFormat = 0,
    numberOfVMetrics = 0,
)

_nameIDs = dict(
             copyright = 0,
            familyName = 1,
             styleName = 2,
            identifier = 3,
              fullName = 4,
               version = 5,
                psName = 6,
             trademark = 7,
          manufacturer = 8,
     typographicFamily = 16,
  typographicSubfamily = 17,
# XXX this needs to be extended with legal things, etc.
)

_panoseDefaults = dict(
    bFamilyType = 0,
    bSerifStyle = 0,
    bWeight = 0,
    bProportion = 0,
    bContrast = 0,
    bStrokeVariation = 0,
    bArmStyle = 0,
    bLetterForm = 0,
    bMidline = 0,
    bXHeight = 0,
)

_OS2Defaults = dict(
    version = 3,
    xAvgCharWidth = 0,
    usWeightClass = 400,
    usWidthClass = 5,
    fsType = 0x0004,  # default: Preview & Print embedding
    ySubscriptXSize = 0,
    ySubscriptYSize = 0,
    ySubscriptXOffset = 0,
    ySubscriptYOffset = 0,
    ySuperscriptXSize = 0,
    ySuperscriptYSize = 0,
    ySuperscriptXOffset = 0,
    ySuperscriptYOffset = 0,
    yStrikeoutSize = 0,
    yStrikeoutPosition = 0,
    sFamilyClass = 0,
    panose = _panoseDefaults,
    ulUnicodeRange1 = 0,
    ulUnicodeRange2 = 0,
    ulUnicodeRange3 = 0,
    ulUnicodeRange4 = 0,
    achVendID = "????",
    fsSelection = 0,
    usFirstCharIndex = 0,
    usLastCharIndex = 0,
    sTypoAscender = 0,
    sTypoDescender = 0,
    sTypoLineGap = 0,
    usWinAscent = 0,
    usWinDescent = 0,
    ulCodePageRange1 = 0,
    ulCodePageRange2 = 0,
    sxHeight = 0,
    sCapHeight = 0,
    usDefaultChar = 0,  # .notdef
    usBreakChar = 32,   # space
    usMaxContext = 2,   # just kerning
    usLowerOpticalPointSize = 0,
    usUpperOpticalPointSize = 0,
)


class FontBuilder(object):

    def __init__(self, unitsPerEm=None, font=None, isTTF=True):
        """Initialize a FontBuilder instance.

        If the `font` argument is not given, a new `TTFont` will be
        constructed, and `unitsPerEm` must be given. If `isTTF` is True,
        the font will be a glyf-based TTF; if `isTTF` is False it will be
        a CFF-based OTF.

        If `font` is given, it must be a `TTFont` instance and `unitsPerEm`
        must _not_ be given. The `isTTF` argument will be ignored.
        """
        if font is None:
            self.font = TTFont(recalcTimestamp=False)
            self.isTTF = isTTF
            now = timestampNow()
            assert unitsPerEm is not None
            self.setupHead(unitsPerEm=unitsPerEm, created=now, modified=now)
            self.setupMaxp()
        else:
            assert unitsPerEm is None
            self.font = font
            self.isTTF = "glyf" in font

    def save(self, path):
        self.font.save(path)

    def _initTableWithValues(self, tableTag, defaults, values):
        table = self.font[tableTag] = newTable(tableTag)
        for k, v in defaults.items():
            setattr(table, k, v)
        for k, v in values.items():
            setattr(table, k, v)
        return table

    def _updateTableWithValues(self, tableTag, values):
        table = self.font[tableTag]
        for k, v in values.items():
            setattr(table, k, v)

    def setupHead(self, **values):
        self._initTableWithValues("head", _headDefaults, values)

    def updateHead(self, **values):
        self._updateTableWithValues("head", values)

    def setupGlyphOrder(self, glyphOrder):
        self.font.setGlyphOrder(glyphOrder)

    def setupCharacterMap(self, cmapping, allowFallback=False):
        subTables = []
        highestUnicode = max(cmapping)
        if highestUnicode > 0xffff:
            cmapping_3_1 = dict((k, v) for k, v in cmapping.items() if k < 0x10000)
            subTable_3_10 = buildCmapSubTable(cmapping, 12, 3, 10)
            subTables.append(subTable_3_10)
        else:
            cmapping_3_1 = cmapping
        format = 4
        subTable_3_1 = buildCmapSubTable(cmapping_3_1, format, 3, 1)
        try:
            subTable_3_1.compile(self.font)
        except struct.error:
            # format 4 overflowed, fall back to format 12
            if not allowFallback:
                raise ValueError("cmap format 4 subtable overflowed; sort glyph order by unicode to fix.")
            format = 12
            subTable_3_1 = buildCmapSubTable(cmapping_3_1, format, 3, 1)
        subTables.append(subTable_3_1)
        subTable_0_3 = buildCmapSubTable(cmapping_3_1, format, 0, 3)
        subTables.append(subTable_0_3)

        self.font["cmap"] = newTable("cmap")
        self.font["cmap"].tableVersion = 0
        self.font["cmap"].tables = subTables

    def setupNameTable(self, nameStrings):
        nameTable = self.font["name"] = newTable("name")
        nameTable.names = []

        for nameName, nameValue in nameStrings.items():
            if isinstance(nameName, int):
                nameID = nameName
            else:
                nameID = _nameIDs[nameName]
            if isinstance(nameValue, basestring):
                nameValue = dict(en=nameValue)
            nameTable.addMultilingualName(nameValue, ttFont=self.font, nameID=nameID)

    def setupOS2(self, **values):
        if "xAvgCharWidth" not in values:
            gs = self.font.getGlyphSet()
            widths = [gs[glyphName].width for glyphName in gs.keys() if gs[glyphName].width > 0]
            values["xAvgCharWidth"] = int(round(sum(widths) / float(len(widths))))
        self._initTableWithValues("OS/2", _OS2Defaults, values)
        if not ("ulUnicodeRange1" in values or "ulUnicodeRange2" in values or
                "ulUnicodeRange3" in values or "ulUnicodeRange3" in values):
            assert "cmap" in self.font, "the 'cmap' table must be setup before the 'OS/2' table"
            self.font["OS/2"].recalcUnicodeRanges(self.font)

    def setupCFF(self, psName, fontInfo, charStringsDict, privateDict):
        assert not self.isTTF
        from .cffLib import CFFFontSet, TopDictIndex, TopDict, CharStrings, \
                GlobalSubrsIndex, PrivateDict
        self.font.sfntVersion = "OTTO"
        fontSet = CFFFontSet()
        fontSet.major = 1
        fontSet.minor = 0
        fontSet.fontNames = [psName]
        fontSet.topDictIndex = TopDictIndex()

        globalSubrs = GlobalSubrsIndex()
        fontSet.GlobalSubrs = globalSubrs
        private = PrivateDict()
        for key, value in privateDict.items():
            setattr(private, key, value)
        fdSelect = None
        fdArray = None

        topDict = TopDict()
        topDict.charset = self.font.getGlyphOrder()
        topDict.Private = private
        for key, value in fontInfo.items():
            setattr(topDict, key, value)

        charStrings = CharStrings(None, topDict.charset, globalSubrs, private, fdSelect, fdArray)
        for glypnName, charString in charStringsDict.items():
            charString.private = private
            charString.globalSubrs = globalSubrs
            charStrings[glypnName] = charString
        topDict.CharStrings = charStrings

        fontSet.topDictIndex.append(topDict)

        self.font["CFF "] = newTable("CFF ")
        self.font["CFF "].cff = fontSet

    def setupGlyf(self, glyphs, calcGlyphBounds=True):
        assert self.isTTF
        self.font["loca"] = newTable("loca")
        self.font["glyf"] = newTable("glyf")
        self.font["glyf"].glyphs = glyphs
        if hasattr(self.font, "glyphOrder"):
            self.font["glyf"].glyphOrder = self.font.glyphOrder
        if calcGlyphBounds:
            self.calcGlyphBounds()

    def setupFvar(self, axes, instances):
        addFvar(self.font, axes, instances)

    def setupGvar(self, variations):
        gvar = self.font["gvar"] = newTable('gvar')
        gvar.version = 1
        gvar.reserved = 0
        gvar.variations = variations

    def calcGlyphBounds(self):
        glyphTable = self.font["glyf"]
        for glyph in glyphTable.glyphs.values():
            glyph.recalcBounds(glyphTable)

    def setupMetrics(self, tableTag, metrics):
        assert tableTag in ("hmtx", "vmtx")
        mtxTable = self.font[tableTag] = newTable(tableTag)
        roundedMetrics = {}
        for gn in metrics:
            w, lsb = metrics[gn]
            roundedMetrics[gn] = int(round(w)), int(round(lsb))
        mtxTable.metrics = roundedMetrics

    def setupHorizontalHeader(self, **values):
        self._initTableWithValues("hhea", _hheaDefaults, values)

    def setupVerticalHeader(self, **values):
        self._initTableWithValues("vhea", _vheaDefaults, values)

    def setupVerticalOrigins(self, verticalOrigins, defaultVerticalOrigin=None):
        if defaultVerticalOrigin is None:
            # find the most frequent vorg value
            bag = {}
            for gn in verticalOrigins:
                vorg = verticalOrigins[gn]
                if vorg not in bag:
                    bag[vorg] = 1
                else:
                    bag[vorg] += 1
            defaultVerticalOrigin = sorted(bag, key=lambda vorg: bag[vorg], reverse=True)[0]
        self._initTableWithValues("VORG", {}, dict(VOriginRecords={}, defaultVertOriginY=defaultVerticalOrigin))
        vorgTable = self.font["VORG"]
        vorgTable.majorVersion = 1
        vorgTable.minorVersion = 0
        for gn in verticalOrigins:
            vorgTable[gn] = verticalOrigins[gn]

    def setupPost(self, keepGlyphNames=True, **values):
        postTable = self._initTableWithValues("post", _postDefaults, values)
        if self.isTTF and keepGlyphNames:
            postTable.formatType = 2.0
            postTable.extraNames = []
            postTable.mapping = {}
        else:
            postTable.formatType = 3.0

    def setupMaxp(self):
        if self.isTTF:
            defaults = _maxpDefaultsTTF
        else:
            defaults = _maxpDefaultsOTF
        self._initTableWithValues("maxp", defaults, {})

    def setupDummyDSIG(self):
        """This adds a dummy DSIG table to the font to make some MS applications
        happy. This does not properly sign the font.
        """
        from .ttLib.tables.D_S_I_G_ import SignatureRecord

        sig = SignatureRecord()
        sig.ulLength = 20
        sig.cbSignature = 12
        sig.usReserved2 = 0
        sig.usReserved1 = 0
        sig.pkcs7 = b'\xd3M4\xd3M5\xd3M4\xd3M4'
        sig.ulFormat = 1
        sig.ulOffset = 20

        values = dict(
            ulVersion = 1,
            usFlag = 1,
            usNumSigs = 1,
            signatureRecords = [sig],
        )
        self._initTableWithValues("DSIG", {}, values)

    def addOpenTypeFeatures(self, features, filename=None, tables=None):
        from .feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(self.font, features, filename=filename, tables=tables)


def buildCmapSubTable(cmapping, format, platformID, platEncID):
    subTable = cmap_classes[format](format)
    subTable.cmap = cmapping
    subTable.platformID = platformID
    subTable.platEncID = platEncID
    subTable.language = 0
    return subTable


def addFvar(font, axes, instances):
    from .misc.py23 import Tag, tounicode
    from .ttLib.tables._f_v_a_r import Axis, NamedInstance

    assert axes

    fvar = newTable('fvar')
    nameTable = font['name']

    for tag, minValue, defaultValue, maxValue, name in axes:
        axis = Axis()
        axis.axisTag = Tag(tag)
        axis.minValue, axis.defaultValue, axis.maxValue = minValue, defaultValue, maxValue
        axis.axisNameID = nameTable.addName(tounicode(name))
        fvar.axes.append(axis)

    for instance in instances:
        coordinates = instance['location']
        name = tounicode(instance['stylename'])
        psname = instance.get('postscriptfontname')

        inst = NamedInstance()
        inst.subfamilyNameID = nameTable.addName(name)
        if psname is not None:
            psname = tounicode(psname)
            inst.postscriptNameID = nameTable.addName(psname)
        inst.coordinates = coordinates
        fvar.instances.append(inst)

    font['fvar'] = fvar
