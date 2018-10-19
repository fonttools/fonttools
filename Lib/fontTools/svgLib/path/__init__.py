from __future__ import (
    print_function, division, absolute_import, unicode_literals)
from fontTools.misc.py23 import *

from fontTools.pens.transformPen import TransformPen
from fontTools.misc import etree
from .parser import parse_path


__all__ = [tostr(s) for s in ("SVGPath", "parse_path")]


class SVGPath(object):
    """ Parse SVG ``path`` elements from a file or string, and draw them
    onto a glyph object that supports the FontTools Pen protocol.

    For example, reading from an SVG file and drawing to a Defcon Glyph:

        import defcon
        glyph = defcon.Glyph()
        pen = glyph.getPen()
        svg = SVGPath("path/to/a.svg")
        svg.draw(pen)

    Or reading from a string containing SVG data, using the alternative
    'fromstring' (a class method):

        data = '<?xml version="1.0" ...'
        svg = SVGPath.fromstring(data)
        svg.draw(pen)

    Both constructors can optionally take a 'transform' matrix (6-float
    tuple, or a FontTools Transform object) to modify the draw output.
    """

    def __init__(self, filename=None, transform=None):
        if filename is None:
            self.root = etree.ElementTree()
        else:
            tree = etree.parse(filename)
            self.root = tree.getroot()
        self.transform = transform

    @classmethod
    def fromstring(cls, data, transform=None):
        self = cls(transform=transform)
        self.root = etree.fromstring(data)
        return self

    def draw(self, pen):
        if self.transform:
            pen = TransformPen(pen, self.transform)
        for el in self.root.findall(".//{http://www.w3.org/2000/svg}path[@d]"):
            parse_path(el.get("d"), pen)
