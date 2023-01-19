"""fontTools.ttLib -- a package for dealing with TrueType fonts."""

from fontTools.misc.loggingTools import deprecateFunction
import logging
import sys


log = logging.getLogger(__name__)


class TTLibError(Exception):
    pass


class TTLibFileIsCollectionError(TTLibError):
    pass


@deprecateFunction("use logging instead", category=DeprecationWarning)
def debugmsg(msg):
    import time

    print(msg + time.strftime("  (%H:%M:%S)", time.localtime(time.time())))


from fontTools.ttLib.ttFont import *
from fontTools.ttLib.ttCollection import TTCollection


def main(args=None):
    """Open/save fonts with TTFont() or TTCollection()

      ./fonttools ttLib [-oFILE] [-yNUMBER] files...

    If multiple files are given on the command-line,
    they are each opened (as a font or collection),
    and added to the font list.

    If -o (output-file) argument is given, the font
    list is then saved to the output file, either as
    a single font, if there is only one font, or as
    a collection otherwise.

    If -y (font-number) argument is given, only the
    specified font from collections is opened.

    The above allow extracting a single font from a
    collection, or combining multiple fonts into a
    collection.

    If --lazy or --no-lazy are give, those are passed
    to the TTFont() or TTCollection() constructors.
    """
    from fontTools import configLogger

    if args is None:
        args = sys.argv[1:]

    import argparse

    parser = argparse.ArgumentParser(
        "fonttools ttLib",
        description="Open/save fonts with TTFont() or TTCollection()",
        epilog="""
		If multiple files are given on the command-line,
		they are each opened (as a font or collection),
		and added to the font list.

		The above, when combined with -o / --output,
		allows for extracting a single font from a
		collection, or combining multiple fonts into a
		collection.
		""",
    )
    parser.add_argument("font", metavar="font", nargs="*", help="Font file.")
    parser.add_argument(
        "-o", "--output", metavar="FILE", default=None, help="Output file."
    )
    parser.add_argument(
        "-y", metavar="NUMBER", default=-1, help="Font number to load from collections."
    )
    parser.add_argument(
        "--lazy", action="store_true", default=None, help="Load fonts lazily."
    )
    parser.add_argument(
        "--no-lazy", dest="lazy", action="store_false", help="Load fonts immediately."
    )
    parser.add_argument(
        "--flavor",
        dest="flavor",
        default=None,
        help="Flavor of output font. 'woff' or 'woff2'.",
    )
    options = parser.parse_args(args)

    fontNumber = int(options.y) if options.y is not None else None
    outFile = options.output
    lazy = options.lazy
    flavor = options.flavor

    fonts = []
    for f in options.font:
        try:
            font = TTFont(f, fontNumber=fontNumber, lazy=lazy)
            fonts.append(font)
        except TTLibFileIsCollectionError:
            collection = TTCollection(f, lazy=lazy)
            fonts.extend(collection.fonts)

    if outFile is not None:
        if len(fonts) == 1:
            fonts[0].flavor = flavor
            fonts[0].save(outFile)
        else:
            if flavor is not None:
                raise TTLibError("Cannot set flavor for collections.")
            collection = TTCollection()
            collection.fonts = fonts
            collection.save(outFile)


if __name__ == "__main__":
    sys.exit(main())
