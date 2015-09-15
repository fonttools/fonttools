#!/usr/bin/env python
from __future__ import print_function
import sys
import os
from fontTools.ttLib import TTFont
from fontTools.ttx import makeOutputFileName


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) < 1:
        print("One argument, the input filename, must be provided.", file=sys.stderr)
        sys.exit(1)

    filename = args[0]
    outfilename = makeOutputFileName(filename, outputDir=None, extension='.woff2')

    print("Processing %s => %s" % (filename, outfilename))

    font = TTFont(filename, recalcBBoxes=False, recalcTimestamp=False)
    font.flavor = "woff2"
    font.save(outfilename, reorderTables=False)


if __name__ == '__main__':
    main()
