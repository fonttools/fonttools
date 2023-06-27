#!/usr/bin/env python3
"""Script to remove redundant font name table records."""
from fontTools.ttLib import TTFont
import sys


def main():
    if len(sys.argv) != 3:
        print("Usage: python nameClean.py font.ttf out.ttf")
        sys.exit()
    font = TTFont(sys.argv[1])
    font["name"].removeUnusedNames(font)
    font.save(sys.argv[2])


if __name__ == "__main__":
    main()
