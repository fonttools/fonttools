#!/usr/bin/env python
"""
Tools to parse data files from the Unicode Character Database.
"""

from __future__ import print_function, absolute_import, division
from __future__ import unicode_literals
from fontTools.misc.py23 import *

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
from contextlib import closing, contextmanager
import re
from codecs import iterdecode
from os.path import abspath, dirname, join as pjoin, pardir, sep


UNIDATA_URL = "https://unicode.org/Public/UNIDATA/"

# by default save output files to ../Lib/fontTools/unicodedata/
UNIDATA_PATH = pjoin(abspath(dirname(__file__)), pardir,
                     "Lib", "fontTools", "unicodedata") + sep

SRC_ENCODING = "# -*- coding: utf-8 -*-\n"

NOTICE = "# NOTE: This file was auto-generated with MetaTools/buildUCD.py.\n"


@contextmanager
def open_unidata_file(filename):
    """Open a text file from https://unicode.org/Public/UNIDATA/"""
    url = UNIDATA_URL + filename
    with closing(urlopen(url)) as response:
        yield iterdecode(response, encoding="utf-8")


def parse_unidata_header(infile):
    """Read the top header of data files, until the first line
    that does not start with '#'.
    """
    header = []
    line = next(infile)
    while line.startswith("#"):
        header.append(line)
        line = next(infile)
    return "".join(header)


def parse_range_properties(infile):
    """Parse a Unicode data file containing a column with one character or
    a range of characters, and another column containing a property value
    separated by a semicolon. Comments after '#' are ignored.
    """
    ranges = []
    line_regex = re.compile(
        r"^"
        r"([0-9A-F]{4,6})"  # first character code
        r"(?:\.\.([0-9A-F]{4,6}))?"  # optional second character code
        r"\s*;\s*"
        r"([^#]+)")  # everything up to the potential comment
    for line in infile:
        match = line_regex.match(line)
        if not match:
            continue

        first, last, data = match.groups()
        if last is None:
            last = first

        first = int(first, 16)
        last = int(last, 16)
        data = data.rstrip()

        ranges.append((first, last, data))

    return ranges


def build_scripts(output_path=None):
    """Fetch "Scripts.txt" data file, parse the script ranges and write
    them as a list of Python tuples to 'fontTools.unicodedata.scripts'.
    """
    filename = "Scripts.txt"
    with open_unidata_file(filename) as f:
        header = parse_unidata_header(f)
        script_ranges = parse_range_properties(f)

    if not output_path:
        output_path = UNIDATA_PATH + "scripts.py"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(SRC_ENCODING)
        f.write("#\n")
        f.write(NOTICE)
        f.write("# Source: {}{}\n".format(UNIDATA_URL, filename))
        f.write("#\n")
        f.write(header+"\n\n")

        f.write("SCRIPT_RANGES = [\n")
        for first, last, script_name in sorted(script_ranges):
            f.write("    (0x{:X}, 0x{:X}, '{}'),\n".format(
                first, last, tostr(script_name)))
        f.write("]\n")


def main():
    build_scripts()


if __name__ == "__main__":
    import sys
    sys.exit(main())
