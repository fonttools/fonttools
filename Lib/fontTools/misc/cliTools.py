"""Collection of utilities for command-line interfaces and console scripts."""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import os
import re


numberAddedRE = re.compile("#\d+$")


def makeOutputFileName(input, outputDir=None, extension=None, overWrite=False):
    dirName, fileName = os.path.split(input)
    fileName, ext = os.path.splitext(fileName)
    if outputDir:
        dirName = outputDir
    fileName = numberAddedRE.split(fileName)[0]
    if extension is None:
        extension = os.path.splitext(input)[1]
    output = os.path.join(dirName, fileName + extension)
    n = 1
    if not overWrite:
        while os.path.exists(output):
            output = os.path.join(
                dirName, fileName + "#" + repr(n) + extension)
            n += 1
    return output
