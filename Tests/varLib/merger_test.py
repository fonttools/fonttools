from copy import deepcopy
import string
from fontTools.colorLib.builder import LayerListBuilder
from fontTools.misc.testTools import getXML
from fontTools.varLib.merger import COLRVariationMerger
from fontTools.varLib.models import VariationModel
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
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
                    '  <VarIndexBase value="2"/>',
                    "</Paint>",
                ],
                [
                    0,
                    NO_VARIATION_INDEX,
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
                    '  <VarIndexBase/>',
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
