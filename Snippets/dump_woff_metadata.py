from __future__ import print_function
import sys
from fontTools.ttx import makeOutputFileName
from fontTools.ttLib import TTFont


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) < 1:
        print("usage: dump_woff_metadata.py "
              "INPUT.woff [OUTPUT.xml]", file=sys.stderr)
        return 1

    infile = args[0]
    if len(args) > 1:
        outfile = args[1]
    else:
        outfile = makeOutputFileName(infile, None, ".xml")

    font = TTFont(infile)

    if not font.flavorData or not font.flavorData.metaData:
        print("No WOFF metadata")
        return 1

    with open(outfile, "wb") as f:
        f.write(font.flavorData.metaData)


if __name__ == "__main__":
    sys.exit(main())
