import sys
import os
from fontTools.ttx import makeOutputFileName
from fontTools.ttLib import TTFont


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) < 2:
        print("usage: merge_woff_metadata.py METADATA.xml "
              "INPUT.woff [OUTPUT.woff]", file=sys.stderr)
        return 1

    metadata_file = args[0]
    with open(metadata_file, 'rb') as f:
        metadata = f.read()

    infile = args[1]
    if len(args) > 2:
        outfile = args[2]
    else:
        filename, ext = os.path.splitext(infile)
        outfile = makeOutputFileName(filename, None, ext)

    font = TTFont(infile)

    if font.flavor not in ("woff", "woff2"):
        print("Input file is not a WOFF or WOFF2 font", file=sys.stderr)
        return 1

    data = font.flavorData

    # this sets the new WOFF metadata
    data.metaData = metadata

    font.save(outfile)


if __name__ == "__main__":
    sys.exit(main())
