from copy import deepcopy
import string
from fontTools.colorLib.builder import LayerListBuilder, buildCOLR, buildClipList
from fontTools.misc.testTools import getXML
from fontTools.varLib.merger import COLRVariationMerger
from fontTools.varLib.models import VariationModel
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
from io import BytesIO
import pytest


NO_VARIATION_INDEX = ot.NO_VARIATION_INDEX


def dump_xml(table, ttFont=None):
    xml = getXML(table.toXML, ttFont)
    print("[")
    for line in xml:
        print(f"  {line!r},")
    print("]")
    return xml


def compile_decompile(table, ttFont):
    writer = OTTableWriter(tableTag="COLR")
    # compile itself may modify a table, safer to copy it first
    table = deepcopy(table)
    table.compile(writer, ttFont)
    data = writer.getAllData()

    reader = OTTableReader(data, tableTag="COLR")
    table2 = table.__class__()
    table2.decompile(reader, ttFont)

    return table2


@pytest.fixture
def ttFont():
    font = TTFont()
    font.setGlyphOrder([".notdef"] + list(string.ascii_letters))
    return font


def build_paint(data):
    return LayerListBuilder().buildPaint(data)


class COLRVariationMergerTest:
    @pytest.mark.parametrize(
        "paints, expected_xml, expected_varIdxes",
        [
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintSolid),
                        "PaletteIndex": 0,
                        "Alpha": 1.0,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintSolid),
                        "PaletteIndex": 0,
                        "Alpha": 1.0,
                    },
                ],
                [
                    '<Paint Format="2"><!-- PaintSolid -->',
                    '  <PaletteIndex value="0"/>',
                    '  <Alpha value="1.0"/>',
                    "</Paint>",
                ],
                [],
                id="solid-same",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintSolid),
                        "PaletteIndex": 0,
                        "Alpha": 1.0,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintSolid),
                        "PaletteIndex": 0,
                        "Alpha": 0.5,
                    },
                ],
                [
                    '<Paint Format="3"><!-- PaintVarSolid -->',
                    '  <PaletteIndex value="0"/>',
                    '  <Alpha value="1.0"/>',
                    '  <VarIndexBase value="0"/>',
                    "</Paint>",
                ],
                [0],
                id="solid-alpha",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintLinearGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                        "x2": 2,
                        "y2": 2,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintLinearGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.1, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 0.9, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                        "x2": 2,
                        "y2": 2,
                    },
                ],
                [
                    '<Paint Format="5"><!-- PaintVarLinearGradient -->',
                    "  <ColorLine>",
                    '    <Extend value="pad"/>',
                    "    <!-- StopCount=2 -->",
                    '    <ColorStop index="0">',
                    '      <StopOffset value="0.0"/>',
                    '      <PaletteIndex value="0"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="0"/>',
                    "    </ColorStop>",
                    '    <ColorStop index="1">',
                    '      <StopOffset value="1.0"/>',
                    '      <PaletteIndex value="1"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="2"/>',
                    "    </ColorStop>",
                    "  </ColorLine>",
                    '  <x0 value="0"/>',
                    '  <y0 value="0"/>',
                    '  <x1 value="1"/>',
                    '  <y1 value="1"/>',
                    '  <x2 value="2"/>',
                    '  <y2 value="2"/>',
                    "  <VarIndexBase/>",
                    "</Paint>",
                ],
                [0, NO_VARIATION_INDEX, 1, NO_VARIATION_INDEX],
                id="linear_grad-stop-offsets",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintLinearGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                        "x2": 2,
                        "y2": 2,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintLinearGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 0.5},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                        "x2": 2,
                        "y2": 2,
                    },
                ],
                [
                    '<Paint Format="5"><!-- PaintVarLinearGradient -->',
                    "  <ColorLine>",
                    '    <Extend value="pad"/>',
                    "    <!-- StopCount=2 -->",
                    '    <ColorStop index="0">',
                    '      <StopOffset value="0.0"/>',
                    '      <PaletteIndex value="0"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="0"/>',
                    "    </ColorStop>",
                    '    <ColorStop index="1">',
                    '      <StopOffset value="1.0"/>',
                    '      <PaletteIndex value="1"/>',
                    '      <Alpha value="1.0"/>',
                    "      <VarIndexBase/>",
                    "    </ColorStop>",
                    "  </ColorLine>",
                    '  <x0 value="0"/>',
                    '  <y0 value="0"/>',
                    '  <x1 value="1"/>',
                    '  <y1 value="1"/>',
                    '  <x2 value="2"/>',
                    '  <y2 value="2"/>',
                    "  <VarIndexBase/>",
                    "</Paint>",
                ],
                [NO_VARIATION_INDEX, 0],
                id="linear_grad-stop[0].alpha",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintLinearGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                        "x2": 2,
                        "y2": 2,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintLinearGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": -0.5, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 1,
                        "y1": 1,
                        "x2": 2,
                        "y2": -200,
                    },
                ],
                [
                    '<Paint Format="5"><!-- PaintVarLinearGradient -->',
                    "  <ColorLine>",
                    '    <Extend value="pad"/>',
                    "    <!-- StopCount=2 -->",
                    '    <ColorStop index="0">',
                    '      <StopOffset value="0.0"/>',
                    '      <PaletteIndex value="0"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="0"/>',
                    "    </ColorStop>",
                    '    <ColorStop index="1">',
                    '      <StopOffset value="1.0"/>',
                    '      <PaletteIndex value="1"/>',
                    '      <Alpha value="1.0"/>',
                    "      <VarIndexBase/>",
                    "    </ColorStop>",
                    "  </ColorLine>",
                    '  <x0 value="0"/>',
                    '  <y0 value="0"/>',
                    '  <x1 value="1"/>',
                    '  <y1 value="1"/>',
                    '  <x2 value="2"/>',
                    '  <y2 value="2"/>',
                    '  <VarIndexBase value="1"/>',
                    "</Paint>",
                ],
                [
                    0,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    1,
                ],
                id="linear_grad-stop[0].offset-y2",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintRadialGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "x0": 0,
                        "y0": 0,
                        "r0": 0,
                        "x1": 1,
                        "y1": 1,
                        "r1": 1,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintRadialGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.1, "PaletteIndex": 0, "Alpha": 0.6},
                                {"StopOffset": 0.9, "PaletteIndex": 1, "Alpha": 0.7},
                            ],
                        },
                        "x0": -1,
                        "y0": -2,
                        "r0": 3,
                        "x1": -4,
                        "y1": -5,
                        "r1": 6,
                    },
                ],
                [
                    '<Paint Format="7"><!-- PaintVarRadialGradient -->',
                    "  <ColorLine>",
                    '    <Extend value="pad"/>',
                    "    <!-- StopCount=2 -->",
                    '    <ColorStop index="0">',
                    '      <StopOffset value="0.0"/>',
                    '      <PaletteIndex value="0"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="0"/>',
                    "    </ColorStop>",
                    '    <ColorStop index="1">',
                    '      <StopOffset value="1.0"/>',
                    '      <PaletteIndex value="1"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="2"/>',
                    "    </ColorStop>",
                    "  </ColorLine>",
                    '  <x0 value="0"/>',
                    '  <y0 value="0"/>',
                    '  <r0 value="0"/>',
                    '  <x1 value="1"/>',
                    '  <y1 value="1"/>',
                    '  <r1 value="1"/>',
                    '  <VarIndexBase value="4"/>',
                    "</Paint>",
                ],
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                id="radial_grad-all-different",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintSweepGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.REPEAT),
                            "ColorStop": [
                                {"StopOffset": 0.4, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 0.6, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "centerX": 0,
                        "centerY": 0,
                        "startAngle": 0,
                        "endAngle": 180.0,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintSweepGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.REPEAT),
                            "ColorStop": [
                                {"StopOffset": 0.4, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 0.6, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "centerX": 0,
                        "centerY": 0,
                        "startAngle": 90.0,
                        "endAngle": 180.0,
                    },
                ],
                [
                    '<Paint Format="9"><!-- PaintVarSweepGradient -->',
                    "  <ColorLine>",
                    '    <Extend value="repeat"/>',
                    "    <!-- StopCount=2 -->",
                    '    <ColorStop index="0">',
                    '      <StopOffset value="0.4"/>',
                    '      <PaletteIndex value="0"/>',
                    '      <Alpha value="1.0"/>',
                    "      <VarIndexBase/>",
                    "    </ColorStop>",
                    '    <ColorStop index="1">',
                    '      <StopOffset value="0.6"/>',
                    '      <PaletteIndex value="1"/>',
                    '      <Alpha value="1.0"/>',
                    "      <VarIndexBase/>",
                    "    </ColorStop>",
                    "  </ColorLine>",
                    '  <centerX value="0"/>',
                    '  <centerY value="0"/>',
                    '  <startAngle value="0.0"/>',
                    '  <endAngle value="180.0"/>',
                    '  <VarIndexBase value="0"/>',
                    "</Paint>",
                ],
                [NO_VARIATION_INDEX, NO_VARIATION_INDEX, 0, NO_VARIATION_INDEX],
                id="sweep_grad-startAngle",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintSweepGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 1.0},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 1.0},
                            ],
                        },
                        "centerX": 0,
                        "centerY": 0,
                        "startAngle": 0.0,
                        "endAngle": 180.0,
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintSweepGradient),
                        "ColorLine": {
                            "Extend": int(ot.ExtendMode.PAD),
                            "ColorStop": [
                                {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 0.5},
                                {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 0.5},
                            ],
                        },
                        "centerX": 0,
                        "centerY": 0,
                        "startAngle": 0.0,
                        "endAngle": 180.0,
                    },
                ],
                [
                    '<Paint Format="9"><!-- PaintVarSweepGradient -->',
                    "  <ColorLine>",
                    '    <Extend value="pad"/>',
                    "    <!-- StopCount=2 -->",
                    '    <ColorStop index="0">',
                    '      <StopOffset value="0.0"/>',
                    '      <PaletteIndex value="0"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="0"/>',
                    "    </ColorStop>",
                    '    <ColorStop index="1">',
                    '      <StopOffset value="1.0"/>',
                    '      <PaletteIndex value="1"/>',
                    '      <Alpha value="1.0"/>',
                    '      <VarIndexBase value="0"/>',
                    "    </ColorStop>",
                    "  </ColorLine>",
                    '  <centerX value="0"/>',
                    '  <centerY value="0"/>',
                    '  <startAngle value="0.0"/>',
                    '  <endAngle value="180.0"/>',
                    "  <VarIndexBase/>",
                    "</Paint>",
                ],
                [NO_VARIATION_INDEX, 0],
                id="sweep_grad-stops-alpha-reuse-varidxbase",
            ),
            pytest.param(
                [
                    {
                        "Format": int(ot.PaintFormat.PaintTransform),
                        "Paint": {
                            "Format": int(ot.PaintFormat.PaintRadialGradient),
                            "ColorLine": {
                                "Extend": int(ot.ExtendMode.PAD),
                                "ColorStop": [
                                    {
                                        "StopOffset": 0.0,
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    {
                                        "StopOffset": 1.0,
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                ],
                            },
                            "x0": 0,
                            "y0": 0,
                            "r0": 0,
                            "x1": 1,
                            "y1": 1,
                            "r1": 1,
                        },
                        "Transform": {
                            "xx": 1.0,
                            "xy": 0.0,
                            "yx": 0.0,
                            "yy": 1.0,
                            "dx": 0.0,
                            "dy": 0.0,
                        },
                    },
                    {
                        "Format": int(ot.PaintFormat.PaintTransform),
                        "Paint": {
                            "Format": int(ot.PaintFormat.PaintRadialGradient),
                            "ColorLine": {
                                "Extend": int(ot.ExtendMode.PAD),
                                "ColorStop": [
                                    {
                                        "StopOffset": 0.0,
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    {
                                        "StopOffset": 1.0,
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                ],
                            },
                            "x0": 0,
                            "y0": 0,
                            "r0": 0,
                            "x1": 1,
                            "y1": 1,
                            "r1": 1,
                        },
                        "Transform": {
                            "xx": 1.0,
                            "xy": 0.0,
                            "yx": 0.0,
                            "yy": 0.5,
                            "dx": 0.0,
                            "dy": -100.0,
                        },
                    },
                ],
                [
                    '<Paint Format="13"><!-- PaintVarTransform -->',
                    '  <Paint Format="6"><!-- PaintRadialGradient -->',
                    "    <ColorLine>",
                    '      <Extend value="pad"/>',
                    "      <!-- StopCount=2 -->",
                    '      <ColorStop index="0">',
                    '        <StopOffset value="0.0"/>',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </ColorStop>",
                    '      <ColorStop index="1">',
                    '        <StopOffset value="1.0"/>',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </ColorStop>",
                    "    </ColorLine>",
                    '    <x0 value="0"/>',
                    '    <y0 value="0"/>',
                    '    <r0 value="0"/>',
                    '    <x1 value="1"/>',
                    '    <y1 value="1"/>',
                    '    <r1 value="1"/>',
                    "  </Paint>",
                    "  <Transform>",
                    '    <xx value="1.0"/>',
                    '    <yx value="0.0"/>',
                    '    <xy value="0.0"/>',
                    '    <yy value="1.0"/>',
                    '    <dx value="0.0"/>',
                    '    <dy value="0.0"/>',
                    '    <VarIndexBase value="0"/>',
                    "  </Transform>",
                    "</Paint>",
                ],
                [
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    0,
                    NO_VARIATION_INDEX,
                    1,
                ],
                id="transform-yy-dy",
            ),
            pytest.param(
                [
                    {
                        "Format": ot.PaintFormat.PaintTransform,
                        "Paint": {
                            "Format": ot.PaintFormat.PaintSweepGradient,
                            "ColorLine": {
                                "Extend": ot.ExtendMode.PAD,
                                "ColorStop": [
                                    {"StopOffset": 0.0, "PaletteIndex": 0},
                                    {
                                        "StopOffset": 1.0,
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                ],
                            },
                            "centerX": 0,
                            "centerY": 0,
                            "startAngle": 0,
                            "endAngle": 360,
                        },
                        "Transform": (1.0, 0, 0, 1.0, 0, 0),
                    },
                    {
                        "Format": ot.PaintFormat.PaintTransform,
                        "Paint": {
                            "Format": ot.PaintFormat.PaintSweepGradient,
                            "ColorLine": {
                                "Extend": ot.ExtendMode.PAD,
                                "ColorStop": [
                                    {"StopOffset": 0.0, "PaletteIndex": 0},
                                    {
                                        "StopOffset": 1.0,
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                ],
                            },
                            "centerX": 256,
                            "centerY": 0,
                            "startAngle": 0,
                            "endAngle": 360,
                        },
                        # Transform.xx below produces the same VarStore delta as the
                        # above PaintSweepGradient's centerX because, when Fixed16.16
                        # is converted to integer, it becomes:
                        # floatToFixed(1.00390625, 16) == 256
                        # Because there is overlap between the varIdxes of the
                        # PaintVarTransform's Affine2x3 and the PaintSweepGradient's
                        # the VarIndexBase is reused (0 for both)
                        "Transform": (1.00390625, 0, 0, 1.0, 10, 0),
                    },
                ],
                [
                    '<Paint Format="13"><!-- PaintVarTransform -->',
                    '  <Paint Format="9"><!-- PaintVarSweepGradient -->',
                    "    <ColorLine>",
                    '      <Extend value="pad"/>',
                    "      <!-- StopCount=2 -->",
                    '      <ColorStop index="0">',
                    '        <StopOffset value="0.0"/>',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "        <VarIndexBase/>",
                    "      </ColorStop>",
                    '      <ColorStop index="1">',
                    '        <StopOffset value="1.0"/>',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "        <VarIndexBase/>",
                    "      </ColorStop>",
                    "    </ColorLine>",
                    '    <centerX value="0"/>',
                    '    <centerY value="0"/>',
                    '    <startAngle value="0.0"/>',
                    '    <endAngle value="360.0"/>',
                    '    <VarIndexBase value="0"/>',
                    "  </Paint>",
                    "  <Transform>",
                    '    <xx value="1.0"/>',
                    '    <yx value="0.0"/>',
                    '    <xy value="0.0"/>',
                    '    <yy value="1.0"/>',
                    '    <dx value="0.0"/>',
                    '    <dy value="0.0"/>',
                    '    <VarIndexBase value="0"/>',
                    "  </Transform>",
                    "</Paint>",
                ],
                [
                    0,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    NO_VARIATION_INDEX,
                    1,
                    NO_VARIATION_INDEX,
                ],
                id="transform-xx-sweep_grad-centerx-same-varidxbase",
            ),
        ],
    )
    def test_merge_Paint(self, paints, ttFont, expected_xml, expected_varIdxes):
        paints = [build_paint(p) for p in paints]
        out = deepcopy(paints[0])

        model = VariationModel([{}, {"ZZZZ": 1.0}])
        merger = COLRVariationMerger(model, ["ZZZZ"], ttFont)

        merger.mergeThings(out, paints)

        assert compile_decompile(out, ttFont) == out
        assert dump_xml(out, ttFont) == expected_xml
        assert merger.varIdxes == expected_varIdxes

    def test_merge_ClipList(self, ttFont):
        clipLists = [
            buildClipList(clips)
            for clips in [
                {
                    "A": (0, 0, 1000, 1000),
                    "B": (0, 0, 1000, 1000),
                    "C": (0, 0, 1000, 1000),
                    "D": (0, 0, 1000, 1000),
                },
                {
                    # non-default masters' clip boxes can be 'sparse'
                    # (i.e. can omit explicit clip box for some glyphs)
                    # "A": (0, 0, 1000, 1000),
                    "B": (10, 0, 1000, 1000),
                    "C": (20, 20, 1020, 1020),
                    "D": (20, 20, 1020, 1020),
                },
            ]
        ]
        out = deepcopy(clipLists[0])

        model = VariationModel([{}, {"ZZZZ": 1.0}])
        merger = COLRVariationMerger(model, ["ZZZZ"], ttFont)

        merger.mergeThings(out, clipLists)

        assert compile_decompile(out, ttFont) == out
        assert dump_xml(out, ttFont) == [
            '<ClipList Format="1">',
            "  <Clip>",
            '    <Glyph value="A"/>',
            '    <ClipBox Format="1">',
            '      <xMin value="0"/>',
            '      <yMin value="0"/>',
            '      <xMax value="1000"/>',
            '      <yMax value="1000"/>',
            "    </ClipBox>",
            "  </Clip>",
            "  <Clip>",
            '    <Glyph value="B"/>',
            '    <ClipBox Format="2">',
            '      <xMin value="0"/>',
            '      <yMin value="0"/>',
            '      <xMax value="1000"/>',
            '      <yMax value="1000"/>',
            '      <VarIndexBase value="0"/>',
            "    </ClipBox>",
            "  </Clip>",
            "  <Clip>",
            '    <Glyph value="C"/>',
            '    <Glyph value="D"/>',
            '    <ClipBox Format="2">',
            '      <xMin value="0"/>',
            '      <yMin value="0"/>',
            '      <xMax value="1000"/>',
            '      <yMax value="1000"/>',
            '      <VarIndexBase value="4"/>',
            "    </ClipBox>",
            "  </Clip>",
            "</ClipList>",
        ]
        assert merger.varIdxes == [
            0,
            NO_VARIATION_INDEX,
            NO_VARIATION_INDEX,
            NO_VARIATION_INDEX,
            1,
            1,
            1,
            1,
        ]

    @pytest.mark.parametrize(
        "master_layer_reuse",
        [
            pytest.param(False, id="no-reuse"),
            pytest.param(True, id="with-reuse"),
        ],
    )
    @pytest.mark.parametrize(
        "color_glyphs, output_layer_reuse, expected_xml, expected_varIdxes",
        [
            pytest.param(
                [
                    {
                        "A": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                    {
                        "A": {
                            "Format": ot.PaintFormat.PaintColrLayers,
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                ],
                False,
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=1 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="0"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "  <LayerList>",
                    "    <!-- LayerCount=2 -->",
                    '    <Paint index="0" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="1" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    "  </LayerList>",
                    "</COLR>",
                ],
                [],
                id="no-variation",
            ),
            pytest.param(
                [
                    {
                        "A": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "C": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 3,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                    {
                        # NOTE: 'A' is missing from non-default master
                        "C": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 3,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                ],
                False,
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=2 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="0"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="1">',
                    '      <BaseGlyph value="C"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="2"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "  <LayerList>",
                    "    <!-- LayerCount=4 -->",
                    '    <Paint index="0" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="1" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="2" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="3"><!-- PaintVarSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    '        <VarIndexBase value="0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="3" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="3"><!-- PaintVarSolid -->',
                    '        <PaletteIndex value="3"/>',
                    '        <Alpha value="1.0"/>',
                    '        <VarIndexBase value="0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    "  </LayerList>",
                    "</COLR>",
                ],
                [0],
                id="sparse-masters",
            ),
            pytest.param(
                [
                    {
                        "A": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "C": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                # 'C' reuses layers 1-3 from 'A'
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "D": {  # identical to 'C'
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "E": {  # superset of 'C' or 'D'
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 3,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                    {
                        # NOTE: 'A' is missing from non-default master
                        "C": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "D": {  # same as 'C'
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "E": {  # first two layers vary the same way as 'C' or 'D'
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 3,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                ],
                True,  # reuse
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=4 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="3"/>',
                    '        <FirstLayerIndex value="0"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="1">',
                    '      <BaseGlyph value="C"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="3"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="2">',
                    '      <BaseGlyph value="D"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="3"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="3">',
                    '      <BaseGlyph value="E"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="5"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "  <LayerList>",
                    "    <!-- LayerCount=7 -->",
                    '    <Paint index="0" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="1" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="2" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="3" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="3"><!-- PaintVarSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    '        <VarIndexBase value="0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="4" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="3"><!-- PaintVarSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    '        <VarIndexBase value="0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="5" Format="1"><!-- PaintColrLayers -->',
                    '      <NumLayers value="2"/>',
                    '      <FirstLayerIndex value="3"/>',
                    "    </Paint>",
                    '    <Paint index="6" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="3"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    "  </LayerList>",
                    "</COLR>",
                ],
                [0],
                id="sparse-masters-with-reuse",
            ),
            pytest.param(
                [
                    {
                        "A": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "C": {  # 'C' shares layer 1 and 2 with 'A'
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                    {
                        "A": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 0,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 0.9,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                        "C": {
                            "Format": int(ot.PaintFormat.PaintColrLayers),
                            "Layers": [
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 1,
                                        "Alpha": 0.5,
                                    },
                                    "Glyph": "B",
                                },
                                {
                                    "Format": int(ot.PaintFormat.PaintGlyph),
                                    "Paint": {
                                        "Format": int(ot.PaintFormat.PaintSolid),
                                        "PaletteIndex": 2,
                                        "Alpha": 1.0,
                                    },
                                    "Glyph": "B",
                                },
                            ],
                        },
                    },
                ],
                True,
                [
                    # a different Alpha variation is applied to a shared layer between
                    # 'A' and 'C' and thus they are no longer shared.
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=2 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="3"/>',
                    '        <FirstLayerIndex value="0"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="1">',
                    '      <BaseGlyph value="C"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="3"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "  <LayerList>",
                    "    <!-- LayerCount=5 -->",
                    '    <Paint index="0" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="1" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="3"><!-- PaintVarSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    '        <VarIndexBase value="0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="2" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="3" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="3"><!-- PaintVarSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    '        <VarIndexBase value="1"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="4" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    "  </LayerList>",
                    "</COLR>",
                ],
                [0, 1],
                id="shared-master-layers-different-variations",
            ),
        ],
    )
    def test_merge_full_table(
        self,
        color_glyphs,
        ttFont,
        expected_xml,
        expected_varIdxes,
        master_layer_reuse,
        output_layer_reuse,
    ):
        master_ttfs = [deepcopy(ttFont) for _ in range(len(color_glyphs))]
        for ttf, glyphs in zip(master_ttfs, color_glyphs):
            # merge algorithm is expected to work the same even if the master COLRs
            # may differ as to the layer reuse, hence we try both ways
            ttf["COLR"] = buildCOLR(glyphs, allowLayerReuse=master_layer_reuse)
        vf = deepcopy(master_ttfs[0])

        model = VariationModel([{}, {"ZZZZ": 1.0}])
        merger = COLRVariationMerger(
            model, ["ZZZZ"], vf, allowLayerReuse=output_layer_reuse
        )

        merger.mergeTables(vf, master_ttfs)

        out = vf["COLR"].table

        assert compile_decompile(out, vf) == out
        assert dump_xml(out, vf) == expected_xml
        assert merger.varIdxes == expected_varIdxes

    @pytest.mark.parametrize(
        "color_glyphs, before_xml, expected_xml",
        [
            pytest.param(
                {
                    "A": {
                        "Format": int(ot.PaintFormat.PaintColrLayers),
                        "Layers": [
                            {
                                "Format": int(ot.PaintFormat.PaintGlyph),
                                "Paint": {
                                    "Format": int(ot.PaintFormat.PaintSolid),
                                    "PaletteIndex": 0,
                                    "Alpha": 1.0,
                                },
                                "Glyph": "B",
                            },
                            {
                                "Format": int(ot.PaintFormat.PaintGlyph),
                                "Paint": {
                                    "Format": int(ot.PaintFormat.PaintSolid),
                                    "PaletteIndex": 1,
                                    "Alpha": 1.0,
                                },
                                "Glyph": "C",
                            },
                            {
                                "Format": int(ot.PaintFormat.PaintGlyph),
                                "Paint": {
                                    "Format": int(ot.PaintFormat.PaintSolid),
                                    "PaletteIndex": 2,
                                    "Alpha": 1.0,
                                },
                                "Glyph": "D",
                            },
                        ],
                    },
                    "E": {
                        "Format": int(ot.PaintFormat.PaintColrLayers),
                        "Layers": [
                            {
                                "Format": int(ot.PaintFormat.PaintGlyph),
                                "Paint": {
                                    "Format": int(ot.PaintFormat.PaintSolid),
                                    "PaletteIndex": 1,
                                    "Alpha": 1.0,
                                },
                                "Glyph": "C",
                            },
                            {
                                "Format": int(ot.PaintFormat.PaintGlyph),
                                "Paint": {
                                    "Format": int(ot.PaintFormat.PaintSolid),
                                    "PaletteIndex": 2,
                                    "Alpha": 1.0,
                                },
                                "Glyph": "D",
                            },
                            {
                                "Format": int(ot.PaintFormat.PaintGlyph),
                                "Paint": {
                                    "Format": int(ot.PaintFormat.PaintSolid),
                                    "PaletteIndex": 3,
                                    "Alpha": 1.0,
                                },
                                "Glyph": "F",
                            },
                        ],
                    },
                    "G": {
                        "Format": int(ot.PaintFormat.PaintColrGlyph),
                        "Glyph": "E",
                    },
                },
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=3 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="3"/>',
                    '        <FirstLayerIndex value="0"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="1">',
                    '      <BaseGlyph value="E"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="2"/>',
                    '        <FirstLayerIndex value="3"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="2">',
                    '      <BaseGlyph value="G"/>',
                    '      <Paint Format="11"><!-- PaintColrGlyph -->',
                    '        <Glyph value="E"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "  <LayerList>",
                    "    <!-- LayerCount=5 -->",
                    '    <Paint index="0" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="1" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="C"/>',
                    "    </Paint>",
                    '    <Paint index="2" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="D"/>',
                    "    </Paint>",
                    '    <Paint index="3" Format="1"><!-- PaintColrLayers -->',
                    '      <NumLayers value="2"/>',
                    '      <FirstLayerIndex value="1"/>',
                    "    </Paint>",
                    '    <Paint index="4" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="3"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="F"/>',
                    "    </Paint>",
                    "  </LayerList>",
                    "</COLR>",
                ],
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=3 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="3"/>',
                    '        <FirstLayerIndex value="0"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="1">',
                    '      <BaseGlyph value="E"/>',
                    '      <Paint Format="1"><!-- PaintColrLayers -->',
                    '        <NumLayers value="3"/>',
                    '        <FirstLayerIndex value="3"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    '    <BaseGlyphPaintRecord index="2">',
                    '      <BaseGlyph value="G"/>',
                    '      <Paint Format="11"><!-- PaintColrGlyph -->',
                    '        <Glyph value="E"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "  <LayerList>",
                    "    <!-- LayerCount=6 -->",
                    '    <Paint index="0" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="0"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="B"/>',
                    "    </Paint>",
                    '    <Paint index="1" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="C"/>',
                    "    </Paint>",
                    '    <Paint index="2" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="D"/>',
                    "    </Paint>",
                    '    <Paint index="3" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="1"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="C"/>',
                    "    </Paint>",
                    '    <Paint index="4" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="2"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="D"/>',
                    "    </Paint>",
                    '    <Paint index="5" Format="10"><!-- PaintGlyph -->',
                    '      <Paint Format="2"><!-- PaintSolid -->',
                    '        <PaletteIndex value="3"/>',
                    '        <Alpha value="1.0"/>',
                    "      </Paint>",
                    '      <Glyph value="F"/>',
                    "    </Paint>",
                    "  </LayerList>",
                    "</COLR>",
                ],
                id="simple-reuse",
            ),
            pytest.param(
                {
                    "A": {
                        "Format": int(ot.PaintFormat.PaintGlyph),
                        "Paint": {
                            "Format": int(ot.PaintFormat.PaintSolid),
                            "PaletteIndex": 0,
                            "Alpha": 1.0,
                        },
                        "Glyph": "B",
                    },
                },
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=1 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="10"><!-- PaintGlyph -->',
                    '        <Paint Format="2"><!-- PaintSolid -->',
                    '          <PaletteIndex value="0"/>',
                    '          <Alpha value="1.0"/>',
                    "        </Paint>",
                    '        <Glyph value="B"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "</COLR>",
                ],
                [
                    "<COLR>",
                    '  <Version value="1"/>',
                    "  <!-- BaseGlyphRecordCount=0 -->",
                    "  <!-- LayerRecordCount=0 -->",
                    "  <BaseGlyphList>",
                    "    <!-- BaseGlyphCount=1 -->",
                    '    <BaseGlyphPaintRecord index="0">',
                    '      <BaseGlyph value="A"/>',
                    '      <Paint Format="10"><!-- PaintGlyph -->',
                    '        <Paint Format="2"><!-- PaintSolid -->',
                    '          <PaletteIndex value="0"/>',
                    '          <Alpha value="1.0"/>',
                    "        </Paint>",
                    '        <Glyph value="B"/>',
                    "      </Paint>",
                    "    </BaseGlyphPaintRecord>",
                    "  </BaseGlyphList>",
                    "</COLR>",
                ],
                id="no-layer-list",
            ),
        ],
    )
    def test_expandPaintColrLayers(
        self, color_glyphs, ttFont, before_xml, expected_xml
    ):
        colr = buildCOLR(color_glyphs, allowLayerReuse=True)

        assert dump_xml(colr.table, ttFont) == before_xml

        before_layer_count = 0
        reuses_colr_layers = False
        if colr.table.LayerList:
            before_layer_count = len(colr.table.LayerList.Paint)
            reuses_colr_layers = any(
                p.Format == ot.PaintFormat.PaintColrLayers
                for p in colr.table.LayerList.Paint
            )

        COLRVariationMerger.expandPaintColrLayers(colr.table)

        assert dump_xml(colr.table, ttFont) == expected_xml

        after_layer_count = (
            0 if not colr.table.LayerList else len(colr.table.LayerList.Paint)
        )

        if reuses_colr_layers:
            assert not any(
                p.Format == ot.PaintFormat.PaintColrLayers
                for p in colr.table.LayerList.Paint
            )
            assert after_layer_count > before_layer_count
        else:
            assert after_layer_count == before_layer_count

        if colr.table.LayerList:
            assert len({id(p) for p in colr.table.LayerList.Paint}) == after_layer_count


class SparsePositioningMergerTest:
    def test_zero_kern_at_default(self):
        # https://github.com/fonttools/fonttools/issues/3111

        pytest.importorskip("ufo2ft")
        pytest.importorskip("ufoLib2")

        from fontTools.designspaceLib import DesignSpaceDocument
        from ufo2ft import compileVariableTTF
        from ufoLib2 import Font

        ds = DesignSpaceDocument()
        ds.addAxisDescriptor(
            name="wght", tag="wght", minimum=100, maximum=900, default=400
        )
        ds.addSourceDescriptor(font=Font(), location=dict(wght=100))
        ds.addSourceDescriptor(font=Font(), location=dict(wght=400))
        ds.addSourceDescriptor(font=Font(), location=dict(wght=900))

        ds.sources[0].font.newGlyph("a").unicode = ord("a")
        ds.sources[0].font.newGlyph("b").unicode = ord("b")
        ds.sources[0].font.features.text = "feature kern { pos a b b' 100; } kern;"

        ds.sources[1].font.newGlyph("a").unicode = ord("a")
        ds.sources[1].font.newGlyph("b").unicode = ord("b")
        ds.sources[1].font.features.text = "feature kern { pos a b b' 0; } kern;"

        ds.sources[2].font.newGlyph("a").unicode = ord("a")
        ds.sources[2].font.newGlyph("b").unicode = ord("b")
        ds.sources[2].font.features.text = "feature kern { pos a b b' -100; } kern;"

        font = compileVariableTTF(ds, inplace=True)
        b = BytesIO()
        font.save(b)

        assert font["GDEF"].table.VarStore.VarData[0].Item[0] == [100, -100]

    def test_sparse_cursive(self):
        # https://github.com/fonttools/fonttools/issues/3168

        pytest.importorskip("ufo2ft")
        pytest.importorskip("ufoLib2")

        from fontTools.designspaceLib import DesignSpaceDocument
        from ufo2ft import compileVariableTTF
        from ufoLib2 import Font

        ds = DesignSpaceDocument()
        ds.addAxisDescriptor(
            name="wght", tag="wght", minimum=100, maximum=900, default=400
        )
        ds.addSourceDescriptor(font=Font(), location=dict(wght=100))
        ds.addSourceDescriptor(font=Font(), location=dict(wght=400))
        ds.addSourceDescriptor(font=Font(), location=dict(wght=900))

        ds.sources[0].font.newGlyph("a").unicode = ord("a")
        ds.sources[0].font.newGlyph("b").unicode = ord("b")
        ds.sources[0].font.newGlyph("c").unicode = ord("c")
        ds.sources[
            0
        ].font.features.text = """
        feature curs {
          position cursive a <anchor 400 20> <anchor 0 -20>;
          position cursive c <anchor NULL> <anchor 0 -20>;
        } curs;
        """

        ds.sources[1].font.newGlyph("a").unicode = ord("a")
        ds.sources[1].font.newGlyph("b").unicode = ord("b")
        ds.sources[1].font.newGlyph("c").unicode = ord("c")
        ds.sources[
            1
        ].font.features.text = """
        feature curs {
          position cursive a <anchor 500 20> <anchor 0 -20>;
          position cursive b <anchor 50 22> <anchor 0 -10>;
          position cursive c <anchor NULL> <anchor 0 -20>;
        } curs;
        """

        ds.sources[2].font.newGlyph("a").unicode = ord("a")
        ds.sources[2].font.newGlyph("b").unicode = ord("b")
        ds.sources[2].font.newGlyph("c").unicode = ord("c")
        ds.sources[
            2
        ].font.features.text = """
        feature curs {
          position cursive b <anchor 100 40> <anchor 0 -30>;
          position cursive c <anchor NULL> <anchor 0 -20>;
        } curs;
        """

        font = compileVariableTTF(ds, inplace=True)
        b = BytesIO()
        font.save(b)

        assert font["GDEF"].table.VarStore.VarData[0].Item[0] == [-100, 0]
