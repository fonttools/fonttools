#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import configLogger
from fontTools.ttLib import TTFont
from fontTools.ttx import makeOutputFileName
from fontTools.ttLib.woff2 import WOFF2FlavorData
import sys
import logging
import argparse


def woff2_compress(input_file, output_file, transform_tables=None):
    logging.info("Processing %s => %s" % (input_file, output_file))

    font = TTFont(input_file, recalcBBoxes=False, recalcTimestamp=False)
    font.flavor = "woff2"

    if transform_tables is not None:
        font.flavorData = WOFF2FlavorData(transformedTables=transform_tables)

    font.save(output_file, reorderTables=False)


def main(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", metavar="INPUT_FILE")
    parser.add_argument("-o", "--output-file", default=None)

    transform_group = parser.add_argument_group()
    transform_group.add_argument(
        "--no-glyf-transform",
        action="store_true",
        help="Do not transform glyf (and loca) tables",
    )
    transform_group.add_argument(
        "--hmtx-transform",
        action="store_true",
        help="Enable optional transformation for 'hmtx' table",
    )

    logging_group = parser.add_mutually_exclusive_group(required=False)
    logging_group.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )
    logging_group.add_argument(
        "-q", "--quiet", action="store_true", help="Turn verbosity off."
    )
    options = parser.parse_args(args)

    configLogger(
        logger=logging.getLogger(),
        level=("DEBUG" if options.verbose else "ERROR" if options.quiet else "INFO"),
    )

    input_file = options.input_file

    if options.output_file:
        output_file = options.output_file
    else:
        output_file = makeOutputFileName(input_file, outputDir=None, extension=".woff2")

    if options.no_glyf_transform:
        transform_tables = set()
    else:
        transform_tables = {"glyf", "loca"}

    if options.hmtx_transform:
        transform_tables.add("hmtx")

    woff2_compress(input_file, output_file, transform_tables)


if __name__ == "__main__":
    sys.exit(main())
