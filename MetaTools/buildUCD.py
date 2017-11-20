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
import logging
import os
from os.path import abspath, dirname, join as pjoin, pardir, sep


UNIDATA_URL = "https://unicode.org/Public/UNIDATA/"
UNIDATA_LICENSE_URL = "http://unicode.org/copyright.html#License"

# by default save output files to ../Lib/fontTools/unicodedata/
UNIDATA_PATH = pjoin(abspath(dirname(__file__)), pardir,
                     "Lib", "fontTools", "unicodedata") + sep

SRC_ENCODING = "# -*- coding: utf-8 -*-\n"

NOTICE = "# NOTE: This file was auto-generated with MetaTools/buildUCD.py.\n"

MAX_UNICODE = 0x10FFFF

log = logging.getLogger()


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


def parse_range_properties(infile, default="Unknown"):
    """Parse a Unicode data file containing a column with one character or
    a range of characters, and another column containing a property value
    separated by a semicolon. Comments after '#' are ignored.

    If the ranges defined in the data file are not continuous, assign the
    'default' property to the unassigned codepoints.

    Return a list of (start, end, property_name) tuples.
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

    ranges.sort()

    # fill the gaps between explicitly defined ranges
    last_start, last_end = -1, -1
    full_ranges = []
    for start, end, name in ranges:
        assert last_end < start
        assert start <= end
        if start - last_end > 1:
            full_ranges.append((last_end+1, start-1, default))
        full_ranges.append((start, end, name))
        last_start, last_end = start, end
    if last_end != MAX_UNICODE:
        full_ranges.append((last_end+1, MAX_UNICODE, default))

    # reduce total number of ranges by combining continuous ones
    last_start, last_end, last_name = full_ranges.pop(0)
    merged_ranges = []
    for start, end, name in full_ranges:
        if name == last_name:
            continue
        else:
            merged_ranges.append((last_start, start-1, last_name))
            last_start, line_end, last_name = start, end, name
    merged_ranges.append((last_start, MAX_UNICODE, last_name))

    # make sure that the ranges cover the full unicode repertoire
    assert merged_ranges[0][0] == 0
    for (cs, ce, cn), (ns, ne, nn) in zip(merged_ranges, merged_ranges[1:]):
        assert ce+1 == ns
    assert merged_ranges[-1][1] == MAX_UNICODE

    return merged_ranges


def build_scripts(local_ucd=None, output_path=None):
    """Fetch "Scripts.txt" data file from Unicode official website, parse
    the script ranges and write them as a list of Python tuples to
    'fontTools.unicodedata.scripts'.

    To load "Scripts.txt" from a local directory, you can use the
    'local_ucd' argument.
    """
    if not output_path:
        output_path = UNIDATA_PATH + "scripts.py"

    filename = "Scripts.txt"
    if local_ucd:
        log.info("loading %r from local directory %r", filename, local_ucd)
        cm = open(pjoin(local_ucd, filename), "r", encoding="utf-8")
    else:
        log.info("downloading %r from %r", filename, UNIDATA_URL)
        cm = open_unidata_file(filename)

    with cm as f:
        header = parse_unidata_header(f)
        ranges = parse_range_properties(f)

    max_name_length = max(len(n) for _, _, n in ranges)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(SRC_ENCODING)
        f.write("#\n")
        f.write(NOTICE)
        f.write("# Source: {}{}\n".format(UNIDATA_URL, filename))
        f.write("# License: {}\n".format(UNIDATA_LICENSE_URL))
        f.write("#\n")
        f.write(header+"\n\n")

        f.write("SCRIPT_RANGES = [\n")
        for first, last, script_name in ranges:
            f.write("    0x{:0>4X},  # .. 0x{:0>4X} ; {}\n".format(
                first, last, tostr(script_name)))
        f.write("]\n")

        f.write("\n")
        f.write("SCRIPT_NAMES = [\n")
        for first, last, script_name in ranges:
            script_name = "'{}',".format(script_name)
            f.write("    {}  # {:0>4X}..{:0>4X}\n".format(
                script_name.ljust(max_name_length+3), first, last))
        f.write("]\n")

    log.info("saved new file: %r", os.path.normpath(output_path))


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate fontTools.unicodedata from UCD data files")
    parser.add_argument(
        '--ucd-path', help="Path to local folder containing UCD data files")
    parser.add_argument('-q', '--quiet', action="store_true")
    options = parser.parse_args()

    level = "WARNING" if options.quiet else "INFO"
    logging.basicConfig(level=level, format="%(message)s")

    build_scripts(local_ucd=options.ucd_path)


if __name__ == "__main__":
    import sys
    sys.exit(main())
