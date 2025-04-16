from string import ascii_letters
import textwrap

from fontTools.misc.testTools import getXML
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.subset.svg import NAMESPACES, ranges

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


# 'simple' here means one svg document per glyph. The required 'id' attribute
# containing the 'glyphXXX' indices can be either on a child of the root <svg>
# or on the <svg> root itself, so we test with both.
# see https://github.com/fonttools/fonttools/issues/2548


def simple_svg_table_glyph_ids_on_children(empty_svg_font):
    font = empty_svg_font
    svg_docs = font["SVG "].docList
    for i in range(1, 11):
        svg = new_svg()
        etree.SubElement(svg, "path", {"id": f"glyph{i}", "d": f"M{i},{i}"})
        svg_docs.append((etree.tostring(svg).decode(), i, i))
    return font


def simple_svg_table_glyph_ids_on_roots(empty_svg_font):
    font = empty_svg_font
    svg_docs = font["SVG "].docList
    for i in range(1, 11):
        svg = new_svg(id=f"glyph{i}")
        etree.SubElement(svg, "path", {"d": f"M{i},{i}"})
        svg_docs.append((etree.tostring(svg).decode(), i, i))
    return font


def new_svg(**attrs):
    return etree.Element("svg", {"xmlns": NAMESPACES["svg"], **attrs})


def _lines(s):
    return textwrap.dedent(s).splitlines()


@pytest.mark.parametrize(
    "add_svg_table, gids, retain_gids, expected_xml",
    [
        # keep four glyphs in total, don't retain gids, which thus get remapped
        (
            simple_svg_table_glyph_ids_on_children,
            "2,4-6",
            False,
            _lines(
                """\
                <svgDoc endGlyphID="1" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph1" d="M2,2"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="2" startGlyphID="2">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph2" d="M4,4"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="3" startGlyphID="3">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph3" d="M5,5"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="4" startGlyphID="4">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph4" d="M6,6"/></svg>]]>
                </svgDoc>
                """
            ),
        ),
        # same as above but with glyph id attribute in the root <svg> element itself
        # https://github.com/fonttools/fonttools/issues/2548
        (
            simple_svg_table_glyph_ids_on_roots,
            "2,4-6",
            False,
            _lines(
                """\
                <svgDoc endGlyphID="1" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph1"><path d="M2,2"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="2" startGlyphID="2">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph2"><path d="M4,4"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="3" startGlyphID="3">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph3"><path d="M5,5"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="4" startGlyphID="4">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph4"><path d="M6,6"/></svg>]]>
                </svgDoc>
                """
            ),
        ),
        # same four glyphs, but we now retain gids
        (
            simple_svg_table_glyph_ids_on_children,
            "2,4-6",
            True,
            _lines(
                """\
                <svgDoc endGlyphID="2" startGlyphID="2">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph2" d="M2,2"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="4" startGlyphID="4">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph4" d="M4,4"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="5" startGlyphID="5">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph5" d="M5,5"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="6" startGlyphID="6">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><path id="glyph6" d="M6,6"/></svg>]]>
                </svgDoc>
                """
            ),
        ),
        # retain gids like above but with glyph id attribute in the root <svg> element itself
        # https://github.com/fonttools/fonttools/issues/2548
        (
            simple_svg_table_glyph_ids_on_roots,
            "2,4-6",
            True,
            _lines(
                """\
                <svgDoc endGlyphID="2" startGlyphID="2">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph2"><path d="M2,2"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="4" startGlyphID="4">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph4"><path d="M4,4"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="5" startGlyphID="5">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph5"><path d="M5,5"/></svg>]]>
                </svgDoc>
                <svgDoc endGlyphID="6" startGlyphID="6">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" id="glyph6"><path d="M6,6"/></svg>]]>
                </svgDoc>
                """
            ),
        ),
    ],
)
def test_subset_single_glyph_per_svg(
    empty_svg_font, add_svg_table, tmp_path, gids, retain_gids, expected_xml
):
    font = add_svg_table(empty_svg_font)

    svg_font_path = tmp_path / "TestSVG.ttf"
    font.save(svg_font_path)

    subset_path = svg_font_path.with_suffix(".subset.ttf")

    subset.main(
        [
            str(svg_font_path),
            f"--output-file={subset_path}",
            f"--gids={gids}",
            "--retain_gids" if retain_gids else "--no-retain_gids",
        ]
    )
    subset_font = TTFont(subset_path)

    assert getXML(subset_font["SVG "].toXML, subset_font) == expected_xml


# This contains a bunch of cross-references between glyphs, paths, gradients, etc.
# Note the path coordinates are completely made up and not meant to be rendered.
# We only care about the tree structure, not it's visual content.
COMPLEX_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <linearGradient id="lg1" x1="50" x2="50" y1="80" y2="80" gradientUnits="userSpaceOnUse">
      <stop stop-color="#A47B62" offset="0"/>
      <stop stop-color="#AD8264" offset="1.0"/>
    </linearGradient>
    <radialGradient id="rg2" cx="50" cy="50" r="10" gradientUnits="userSpaceOnUse">
      <stop stop-color="#A47B62" offset="0"/>
      <stop stop-color="#AD8264" offset="1.0"/>
    </radialGradient>
    <radialGradient id="rg3" xlink:href="#rg2" r="20"/>
    <radialGradient id="rg4" xlink:href="#rg3" cy="100"/>
    <path id="p1" d="M3,3"/>
    <clipPath id="c1">
      <circle cx="10" cy="10" r="1"/>
    </clipPath>
  </defs>
  <g id="glyph1">
    <g id="glyph2">
      <path d="M0,0"/>
    </g>
    <g>
      <path d="M1,1" fill="url(#lg1)"/>
      <path d="M2,2"/>
    </g>
  </g>
  <g id="glyph3">
    <use xlink:href="#p1"/>
  </g>
  <use id="glyph4" xlink:href="#glyph1" x="10"/>
  <use id="glyph5" xlink:href="#glyph2" y="-10"/>
  <g id="glyph6">
    <use xlink:href="#p1" transform="scale(2, 1)"/>
  </g>
  <g id="group1">
    <g id="glyph7">
      <path id="p2" d="M4,4"/>
    </g>
    <g id=".glyph7">
      <path d="M4,4"/>
    </g>
    <g id="glyph8">
      <g id=".glyph8">
        <path id="p3" d="M5,5"/>
        <path id="M6,6"/>
      </g>
      <path d="M7,7"/>
    </g>
    <g id="glyph9">
      <use xlink:href="#p2"/>
    </g>
    <g id="glyph10">
      <use xlink:href="#p3"/>
    </g>
  </g>
  <g id="glyph11">
    <path d="M7,7" fill="url(#rg4)"/>
  </g>
  <g id="glyph12">
    <path d="M7,7" style="fill:url(#lg1);stroke:red;clip-path:url(#c1)"/>
  </g>
</svg>
"""


@pytest.mark.parametrize(
    "subset_gids, expected_xml",
    [
        # we only keep gid=2, with 'glyph2' defined inside 'glyph1': 'glyph2'
        # is renamed 'glyph1' to match the new subset indices, and the old 'glyph1'
        # is kept (as it contains 'glyph2') but renamed '.glyph1' to avoid clash
        (
            "2",
            _lines(
                """\
                <svgDoc endGlyphID="1" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <g id=".glyph1">
                    <g id="glyph1">
                      <path d="M0,0"/>
                    </g>
                  </g>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
        # we keep both gid 1 and 2: the glyph elements' ids stay as they are (only the
        # range endGlyphID change); a gradient is kept since it's referenced by glyph1
        (
            "1,2",
            _lines(
                """\
                <svgDoc endGlyphID="2" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <defs>
                    <linearGradient id="lg1" x1="50" x2="50" y1="80" y2="80" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#A47B62" offset="0"/>
                      <stop stop-color="#AD8264" offset="1.0"/>
                    </linearGradient>
                  </defs>
                  <g id="glyph1">
                    <g id="glyph2">
                      <path d="M0,0"/>
                    </g>
                    <g>
                      <path d="M1,1" fill="url(#lg1)"/>
                      <path d="M2,2"/>
                    </g>
                  </g>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
        (
            # both gid 3 and 6 refer (via <use xlink:href="#...") to path 'p1', which
            # is thus kept in <defs>; the glyph ids and range start/end are renumbered.
            "3,6",
            _lines(
                """\
                <svgDoc endGlyphID="2" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <defs>
                    <path id="p1" d="M3,3"/>
                  </defs>
                  <g id="glyph1">
                    <use xlink:href="#p1"/>
                  </g>
                  <g id="glyph2">
                    <use xlink:href="#p1" transform="scale(2, 1)"/>
                  </g>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
        (
            # 'glyph4' uses the whole 'glyph1' element (translated); we keep the latter
            # renamed to avoid clashes with new gids
            "3-4",
            _lines(
                """\
                <svgDoc endGlyphID="2" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <defs>
                    <linearGradient id="lg1" x1="50" x2="50" y1="80" y2="80" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#A47B62" offset="0"/>
                      <stop stop-color="#AD8264" offset="1.0"/>
                    </linearGradient>
                    <path id="p1" d="M3,3"/>
                  </defs>
                  <g id=".glyph1">
                    <g id=".glyph2">
                      <path d="M0,0"/>
                    </g>
                    <g>
                      <path d="M1,1" fill="url(#lg1)"/>
                      <path d="M2,2"/>
                    </g>
                  </g>
                  <g id="glyph1">
                    <use xlink:href="#p1"/>
                  </g>
                  <use id="glyph2" xlink:href="#.glyph1" x="10"/>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
        (
            # 'glyph9' uses a path 'p2' defined inside 'glyph7', the latter is excluded
            # from our subset, thus gets renamed '.glyph7'; an unrelated element with
            # same id=".glyph7" doesn't clash because it was dropped.
            # Similarly 'glyph10' uses path 'p3' defined inside 'glyph8', also excluded
            # from subset and prefixed with '.'. But since an id=".glyph8" is already
            # used in the doc, we append a .{digit} suffix to disambiguate.
            "9,10",
            _lines(
                """\
                <svgDoc endGlyphID="2" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <g id="group1">
                    <g id=".glyph7">
                      <path id="p2" d="M4,4"/>
                    </g>
                    <g id=".glyph8.1">
                      <g id=".glyph8">
                        <path id="p3" d="M5,5"/>
                      </g>
                    </g>
                    <g id="glyph1">
                      <use xlink:href="#p2"/>
                    </g>
                    <g id="glyph2">
                      <use xlink:href="#p3"/>
                    </g>
                  </g>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
        (
            # 'glyph11' uses gradient 'rg4' which inherits from 'rg3', which inherits
            # from 'rg2', etc.
            "11",
            _lines(
                """\
                <svgDoc endGlyphID="1" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <defs>
                    <radialGradient id="rg2" cx="50" cy="50" r="10" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#A47B62" offset="0"/>
                      <stop stop-color="#AD8264" offset="1.0"/>
                    </radialGradient>
                    <radialGradient id="rg3" xlink:href="#rg2" r="20"/>
                    <radialGradient id="rg4" xlink:href="#rg3" cy="100"/>
                  </defs>
                  <g id="glyph1">
                    <path d="M7,7" fill="url(#rg4)"/>
                  </g>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
        (
            # 'glyph12' contains a style attribute with inline CSS declarations that
            # contains references to a gradient fill and a clipPath: we keep those
            "12",
            _lines(
                """\
                <svgDoc endGlyphID="1" startGlyphID="1">
                  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <defs>
                    <linearGradient id="lg1" x1="50" x2="50" y1="80" y2="80" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#A47B62" offset="0"/>
                      <stop stop-color="#AD8264" offset="1.0"/>
                    </linearGradient>
                    <clipPath id="c1">
                      <circle cx="10" cy="10" r="1"/>
                    </clipPath>
                  </defs>
                  <g id="glyph1">
                    <path d="M7,7" style="fill:url(#lg1);stroke:red;clip-path:url(#c1)"/>
                  </g>
                </svg>
                ]]>
                </svgDoc>
                """
            ),
        ),
    ],
)
def test_subset_svg_with_references(
    empty_svg_font, tmp_path, subset_gids, expected_xml
):
    font = empty_svg_font

    font["SVG "].docList.append((COMPLEX_SVG, 1, 12))
    svg_font_path = tmp_path / "TestSVG.ttf"
    font.save(svg_font_path)
    subset_path = svg_font_path.with_suffix(".subset.ttf")

    subset.main(
        [
            str(svg_font_path),
            f"--output-file={subset_path}",
            f"--gids={subset_gids}",
            "--pretty-svg",
        ]
    )
    subset_font = TTFont(subset_path)

    if expected_xml is not None:
        assert getXML(subset_font["SVG "].toXML, subset_font) == expected_xml
    else:
        assert "SVG " not in subset_font


def test_subset_svg_empty_table(empty_svg_font, tmp_path):
    font = empty_svg_font

    svg = new_svg()
    etree.SubElement(svg, "rect", {"id": "glyph1", "x": "1", "y": "2"})
    font["SVG "].docList.append((etree.tostring(svg).decode(), 1, 1))

    svg_font_path = tmp_path / "TestSVG.ttf"
    font.save(svg_font_path)
    subset_path = svg_font_path.with_suffix(".subset.ttf")

    # there's no gid=2 in SVG table, drop the empty table
    subset.main([str(svg_font_path), f"--output-file={subset_path}", f"--gids=2"])

    assert "SVG " not in TTFont(subset_path)


def test_subset_svg_missing_glyph(empty_svg_font, tmp_path):
    font = empty_svg_font

    svg = new_svg()
    etree.SubElement(svg, "rect", {"id": "glyph1", "x": "1", "y": "2"})
    font["SVG "].docList.append(
        (
            etree.tostring(svg).decode(),
            1,
            # the range endGlyphID=2 declares two glyphs however our svg contains
            # only one glyph element with id="glyph1", the "glyph2" one is absent.
            # Techically this would be invalid according to the OT-SVG spec.
            2,
        )
    )
    svg_font_path = tmp_path / "TestSVG.ttf"
    font.save(svg_font_path)
    subset_path = svg_font_path.with_suffix(".subset.ttf")

    # make sure we don't crash when we don't find the expected "glyph2" element
    subset.main([str(svg_font_path), f"--output-file={subset_path}", f"--gids=1"])

    subset_font = TTFont(subset_path)
    assert getXML(subset_font["SVG "].toXML, subset_font) == [
        '<svgDoc endGlyphID="1" startGlyphID="1">',
        '  <![CDATA[<svg xmlns="http://www.w3.org/2000/svg"><rect id="glyph1" x="1" y="2"/></svg>]]>',
        "</svgDoc>",
    ]

    # ignore the missing gid even if included in the subset; in this test case we
    # end up with an empty svg document--which is dropped, along with the empty table
    subset.main([str(svg_font_path), f"--output-file={subset_path}", f"--gids=2"])

    assert "SVG " not in TTFont(subset_path)


@pytest.mark.parametrize(
    "ints, expected_ranges",
    [
        ((), []),
        ((0,), [(0, 0)]),
        ((0, 1), [(0, 1)]),
        ((1, 1, 1, 1), [(1, 1)]),
        ((1, 3), [(1, 1), (3, 3)]),
        ((4, 2, 1, 3), [(1, 4)]),
        ((1, 2, 4, 5, 6, 9, 13, 14, 15), [(1, 2), (4, 6), (9, 9), (13, 15)]),
    ],
)
def test_ranges(ints, expected_ranges):
    assert list(ranges(ints)) == expected_ranges
