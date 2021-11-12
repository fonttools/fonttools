from string import ascii_letters

from fontTools.misc.testTools import getXML
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.subset.svg import NAMESPACES

import pytest

etree = pytest.importorskip("lxml.etree")


@pytest.fixture
def empty_svg_font():
    glyph_order = [".notdef"] + list(ascii_letters)

    pen = TTGlyphPen(glyphSet=None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 500))
    pen.lineTo((500, 500))
    pen.lineTo((500, 0))
    pen.closePath()
    glyph = pen.glyph()
    glyphs = {g: glyph for g in glyph_order}

    fb = FontBuilder(unitsPerEm=1024, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({ord(c): c for c in ascii_letters})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (500, 0) for g in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupOS2()
    fb.setupPost()
    fb.setupNameTable({"familyName": "TestSVG", "styleName": "Regular"})

    svg_table = newTable("SVG ")
    svg_table.docList = []
    fb.font["SVG "] = svg_table

    return fb.font


def new_svg(**attrs):
    return etree.Element("svg", {"xmlns": NAMESPACES["svg"], **attrs})


def test_subset_svg_simple(empty_svg_font, tmp_path):
    # 'simple' as in one glyph per svg doc
    font = empty_svg_font

    svg_docs = font["SVG "].docList
    for i in range(1, 11):
        svg = new_svg()
        etree.SubElement(svg, "path", {"id": f"glyph{i}", "d": f"M{i},{i}"})
        svg_docs.append((etree.tostring(svg).decode(), i, i))

    svg_font_path = tmp_path / "TestSVG.ttf"
    font.save(svg_font_path)

    subset_path = svg_font_path.with_suffix(".subset.ttf")

    # keep four glyphs in total, don't retain gids, which thus get remapped
    subset.main(
        [
            str(svg_font_path),
            f"--output-file={subset_path}",
            "--gids=2,4-6",
        ]
    )
    subset_font = TTFont(subset_path)

    assert getXML(subset_font["SVG "].toXML, subset_font) == [
        '<svgDoc endGlyphID="1" startGlyphID="1">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph1" d="M2,2"/></svg>]]>',
        "</svgDoc>",
        '<svgDoc endGlyphID="2" startGlyphID="2">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph2" d="M4,4"/></svg>]]>',
        "</svgDoc>",
        '<svgDoc endGlyphID="3" startGlyphID="3">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph3" d="M5,5"/></svg>]]>',
        "</svgDoc>",
        '<svgDoc endGlyphID="4" startGlyphID="4">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph4" d="M6,6"/></svg>]]>',
        "</svgDoc>",
    ]

    # same four glyphs, now retain gids
    subset.main(
        [
            str(svg_font_path),
            f"--output-file={subset_path}",
            "--gids=2,4-6",
            "--retain-gids",
        ]
    )
    subset_font = TTFont(subset_path)

    assert getXML(subset_font["SVG "].toXML, subset_font) == [
        '<svgDoc endGlyphID="2" startGlyphID="2">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph2" d="M2,2"/></svg>]]>',
        "</svgDoc>",
        '<svgDoc endGlyphID="4" startGlyphID="4">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph4" d="M4,4"/></svg>]]>',
        "</svgDoc>",
        '<svgDoc endGlyphID="5" startGlyphID="5">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph5" d="M5,5"/></svg>]]>',
        "</svgDoc>",
        '<svgDoc endGlyphID="6" startGlyphID="6">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph6" d="M6,6"/></svg>]]>',
        "</svgDoc>",
    ]
