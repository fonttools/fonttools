#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse

from fdiff import __version__


def main():  # pragma: no cover
    run(sys.argv[1:])


def run(argv):
    # ===========================================================
    # argparse command line argument definitions
    # ===========================================================
    parser = argparse.ArgumentParser(
        description="A font OpenType table diff tool"
    )
    parser.add_argument(
        "--version", action="version", version="fdiff v{}".format(__version__)
    )
    parser.add_argument('-c', action='store_true', default=False,
                        help='ANSI escape code colored diff')
    parser.add_argument('-l', '--lines', type=int, default=3,
                        help='Number of context lines (default 3)')
    parser.add_argument('PREFILE',
                        help='Font file path 1')
    parser.add_argument('POSTFILE',
                        help='Font file path 2')

    args = parser.parse_args(argv)
