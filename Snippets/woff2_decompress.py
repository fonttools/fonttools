#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttx import makeOutputFileName
import sys
import os


def make_output_name(filename):
    with open(filename, "rb") as f:
        f.seek(4)
        sfntVersion = f.read(4)
    assert len(sfntVersion) == 4, "not enough data"
    ext = '.ttf' if sfntVersion == b"\x00\x01\x00\x00" else ".otf"
    outfilename = makeOutputFileName(filename, outputDir=None, extension=ext)
    return outfilename


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) < 1:
        print("One argument, the input filename, must be provided.", file=sys.stderr)
        sys.exit(1)

    filename = args[0]
    outfilename = make_output_name(filename)

    print("Processing %s => %s" % (filename, outfilename))

    font = TTFont(filename, recalcBBoxes=False, recalcTimestamp=False)
    font.flavor = None
    font.save(outfilename, reorderTables=True)


if __name__ == '__main__':
    main()
