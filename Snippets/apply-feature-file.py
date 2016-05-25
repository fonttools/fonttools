#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import fontTools.feaLib.builder as feaLibBuilder
from fontTools.ttLib import TTFont
from fontTools import configLogger
import sys
import argparse


parser = argparse.ArgumentParser(
    description="Use fontTools to compile OpenType features.")
parser.add_argument("input_fea", metavar="FEATURES",
                    help="Path to the feature file")
parser.add_argument("input_font", metavar="INPUT",
                    help="Path to the input font")
parser.add_argument("output_font", metavar="OUTPUT",
                    help="Path to the output font")
parser.add_argument("-v", "--verbose", help="increase the logger verbosity. "
                    "Multiple -v options are allowed.", action="count",
                    default=0)
options = parser.parse_args(sys.argv[1:])

levels = ["WARNING", "INFO", "DEBUG"]
configLogger(level=levels[min(len(levels) - 1, options.verbose)])


font = TTFont(options.input_font)
feaLibBuilder.addOpenTypeFeatures(font, options.input_fea)
font.save(options.output_font)
