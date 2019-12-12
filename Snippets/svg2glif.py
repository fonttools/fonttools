#!/usr/bin/env python3
""" Convert SVG paths to UFO glyphs. """


__requires__ = ["fontTools"]

from fontTools.misc.py23 import SimpleNamespace
from fontTools.svgLib import SVGPath

from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.ufoLib.glifLib import writeGlyphToString


__all__ = ["svg2glif"]


def svg2glif(svg, name, width=0, height=0, unicodes=None, transform=None,
             version=2):
    """ Convert an SVG outline to a UFO glyph with given 'name', advance
    'width' and 'height' (int), and 'unicodes' (list of int).
    Return the resulting string in GLIF format (default: version 2).
    If 'transform' is provided, apply a transformation matrix before the
    conversion (must be tuple of 6 floats, or a FontTools Transform object).
    """
    glyph = SimpleNamespace(width=width, height=height, unicodes=unicodes)
    outline = SVGPath.fromstring(svg, transform=transform)

    # writeGlyphToString takes a callable (usually a glyph's drawPoints
    # method) that accepts a PointPen, however SVGPath currently only has
    # a draw method that accepts a segment pen. We need to wrap the call
    # with a converter pen.
    def drawPoints(pointPen):
        pen = SegmentToPointPen(pointPen)
        outline.draw(pen)

    return writeGlyphToString(name,
                              glyphObject=glyph,
                              drawPointsFunc=drawPoints,
                              formatVersion=version)


def parse_args(args):
    import argparse

    def split(arg):
        return arg.replace(",", " ").split()

    def unicode_hex_list(arg):
        try:
            return [int(unihex, 16) for unihex in split(arg)]
        except ValueError:
            msg = "Invalid unicode hexadecimal value: %r" % arg
            raise argparse.ArgumentTypeError(msg)

    def transform_list(arg):
        try:
            return [float(n) for n in split(arg)]
        except ValueError:
            msg = "Invalid transformation matrix: %r" % arg
            raise argparse.ArgumentTypeError(msg)

    parser = argparse.ArgumentParser(
        description="Convert SVG outlines to UFO glyphs (.glif)")
    parser.add_argument(
        "infile", metavar="INPUT.svg", help="Input SVG file containing "
        '<path> elements with "d" attributes.')
    parser.add_argument(
        "outfile", metavar="OUTPUT.glif", help="Output GLIF file (default: "
        "print to stdout)", nargs='?')
    parser.add_argument(
        "-n", "--name", help="The glyph name (default: input SVG file "
        "basename, without the .svg extension)")
    parser.add_argument(
        "-w", "--width", help="The glyph advance width (default: 0)",
        type=int, default=0)
    parser.add_argument(
        "-H", "--height", help="The glyph vertical advance (optional if "
        '"width" is defined)', type=int, default=0)
    parser.add_argument(
        "-u", "--unicodes", help="List of Unicode code points as hexadecimal "
        'numbers (e.g. -u "0041 0042")',
        type=unicode_hex_list)
    parser.add_argument(
        "-t", "--transform", help="Transformation matrix as a list of six "
        'float values (e.g. -t "0.1 0 0 -0.1 -50 200")', type=transform_list)
    parser.add_argument(
        "-f", "--format", help="UFO GLIF format version (default: 2)",
        type=int, choices=(1, 2), default=2)

    return parser.parse_args(args)


def main(args=None):
    from io import open

    options = parse_args(args)

    svg_file = options.infile

    if options.name:
        name = options.name
    else:
        import os
        name = os.path.splitext(os.path.basename(svg_file))[0]

    with open(svg_file, "r", encoding="utf-8") as f:
        svg = f.read()

    glif = svg2glif(svg, name,
                    width=options.width,
                    height=options.height,
                    unicodes=options.unicodes,
                    transform=options.transform,
                    version=options.format)

    if options.outfile is None:
        print(glif)
    else:
        with open(options.outfile, 'w', encoding='utf-8') as f:
            f.write(glif)


if __name__ == "__main__":
    import sys
    sys.exit(main())
