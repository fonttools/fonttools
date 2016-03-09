#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import fontTools.feaLib.builder as feaLibBuilder
from fontTools.ttLib import TTFont
import sys

if len(sys.argv) != 4:
    print("usage: apply-feature-file.py features.fea in.ttf out.ttf")
    sys.exit(1)

inputFeaturePath = sys.argv[1]
inputFontPath = sys.argv[2]
outputFontPath = sys.argv[3]

font = TTFont(inputFontPath)
feaLibBuilder.addOpenTypeFeatures(inputFeaturePath, font)
font.save(outputFontPath)
