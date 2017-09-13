from __future__ import print_function, absolute_import, division

from fontTools.misc.py23 import *
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib import SVGPath

import os
from tempfile import NamedTemporaryFile


SVG_DATA = """\
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
 "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="1000.0" height="1000.0">
<path d="M 100 100 L 300 100 L 200 300 z"/>
<path d="M100,200 C100,100 250,100 250,200 S400,300 400,200"/>
</svg>
"""

EXPECTED_PEN_COMMANDS = [
    ("moveTo", ((100.0, 100.0),)),
    ("lineTo", ((300.0, 100.0),)),
    ("lineTo", ((200.0, 300.0),)),
    ("lineTo", ((100.0, 100.0),)),
    ("closePath", ()),
    ("moveTo", ((100.0, 200.0),)),
    ("curveTo", ((100.0, 100.0),
                 (250.0, 100.0),
                 (250.0, 200.0))),
    ("curveTo", ((250.0, 300.0),
                 (400.0, 300.0),
                 (400.0, 200.0))),
    ("endPath", ())
]


class SVGPathTest(object):

    def test_from_svg_file(self):
        pen = RecordingPen()
        with NamedTemporaryFile(delete=False) as tmp:
            tmp.write(tobytes(SVG_DATA))
        try:
            svg = SVGPath(tmp.name)
            svg.draw(pen)
        finally:
            os.remove(tmp.name)

        assert pen.value == EXPECTED_PEN_COMMANDS

    def test_fromstring(self):
        pen = RecordingPen()
        svg = SVGPath.fromstring(SVG_DATA)
        svg.draw(pen)

        assert pen.value == EXPECTED_PEN_COMMANDS

    def test_transform(self):
        pen = RecordingPen()
        svg = SVGPath.fromstring(SVG_DATA,
                                 transform=(1.0, 0, 0, -1.0, 0, 1000))
        svg.draw(pen)

        assert pen.value == [
            ("moveTo", ((100.0, 900.0),)),
            ("lineTo", ((300.0, 900.0),)),
            ("lineTo", ((200.0, 700.0),)),
            ("lineTo", ((100.0, 900.0),)),
            ("closePath", ()),
            ("moveTo", ((100.0, 800.0),)),
            ("curveTo", ((100.0, 900.0),
                         (250.0, 900.0),
                         (250.0, 800.0))),
            ("curveTo", ((250.0, 700.0),
                         (400.0, 700.0),
                         (400.0, 800.0))),
            ("endPath", ())
        ]
