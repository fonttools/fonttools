from fontTools.varLib import _add_fvar, _add_avar, load_designspace
from fontTools.misc.cliTools import makeOutputFileName
from fontTools import configLogger
from fontTools.ttLib import TTFont, newTable
import logging
import argparse

log = logging.getLogger("fontTools.varLib.avar")


def main(args=None):
    """Add `avar` table from designspace file to variable font."""

    if args is None:
        import sys

        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        "fonttools varLib.avar",
        description="Add `avar` table from designspace file to variable font.",
    )
    parser.add_argument("font", metavar="varfont.ttf", help="Variable-font file.")
    parser.add_argument(
        "designspace",
        metavar="family.designspace",
        help="Designspace file.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output font file name.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )

    options = parser.parse_args(args)

    configLogger(level=("INFO" if options.verbose else "WARNING"))

    font = TTFont(options.font)

    if options.designspace is None:
        from .unbuild import unbuild

        unbuild(font)
        return 0

    ds = load_designspace(options.designspace, require_sources=False)

    if not "fvar" in font:
        # if "name" not in font:
        font["name"] = newTable("name")
        _add_fvar(font, ds.axes, ds.instances)

    axisTags = [a.axisTag for a in font["fvar"].axes]

    if "avar" in font:
        log.warning("avar table already present, overwriting.")
        del font["avar"]

    _add_avar(font, ds.axes, ds.axisMappings, axisTags)

    if options.output_file is None:
        outfile = makeOutputFileName(options.font, overWrite=True, suffix=".avar")
    else:
        outfile = options.output_file
    if outfile:
        log.info("Saving %s", outfile)
        font.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
