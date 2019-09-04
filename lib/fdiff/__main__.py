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
    args = parser.parse_args(argv)
