#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttx import makeOutputFileName
from fontTools.ttLib.woff2 import WOFF2FlavorData
import sys


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    disableTransforms = False
    if "--disable-transforms" in args:
        disableTransforms = True
        args.remove("--disable-transforms")

    if len(args) < 1:
        print("One argument, the input filename, must be provided.", file=sys.stderr)
        return 1

    filename = args[0]
    outfilename = makeOutputFileName(filename, outputDir=None, extension='.woff2')

    print("Processing %s => %s" % (filename, outfilename))

    font = TTFont(filename, recalcBBoxes=False, recalcTimestamp=False)
    font.flavor = "woff2"

    if disableTransforms:
        # an empty tuple signals that we don't want any table to be transformed
        font.flavorData = WOFF2FlavorData(transformedTables=())

    font.save(outfilename, reorderTables=False)


if __name__ == '__main__':
    sys.exit(main())
