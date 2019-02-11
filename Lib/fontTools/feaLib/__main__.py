from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeatures, Builder
from fontTools import configLogger
from fontTools.misc.cliTools import makeOutputFileName
import sys
import argparse
import logging


log = logging.getLogger("fontTools.feaLib")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Use fontTools to compile OpenType feature files (*.fea).")
    parser.add_argument(
        "input_fea", metavar="FEATURES", help="Path to the feature file")
    parser.add_argument(
        "input_font", metavar="INPUT_FONT", help="Path to the input font")
    parser.add_argument(
        "-o", "--output", dest="output_font", metavar="OUTPUT_FONT",
        help="Path to the output font.")
    parser.add_argument(
        "-t", "--tables", metavar="TABLE_TAG", choices=Builder.supportedTables,
        nargs='+', help="Specify the table(s) to be built.")
    parser.add_argument(
        "-v", "--verbose", help="increase the logger verbosity. Multiple -v "
        "options are allowed.", action="count", default=0)
    options = parser.parse_args(args)

    levels = ["WARNING", "INFO", "DEBUG"]
    configLogger(level=levels[min(len(levels) - 1, options.verbose)])

    output_font = options.output_font or makeOutputFileName(options.input_font)
    log.info("Compiling features to '%s'" % (output_font))

    font = TTFont(options.input_font)
    addOpenTypeFeatures(font, options.input_fea, tables=options.tables)
    font.save(output_font)


if __name__ == '__main__':
    sys.exit(main())
