import argparse
import logging
import sys
from io import StringIO
from pathlib import Path

from fontTools import configLogger
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.feaLib.error import FeatureLibError
from fontTools.misc.cliTools import makeOutputFileName
from fontTools.ttLib import TTFont, TTLibError
from fontTools.voltLib.parser import Parser
from fontTools.voltLib.voltToFea import TABLES, VoltToFea

log = logging.getLogger("fontTools.feaLib")

SUPPORTED_TABLES = TABLES + ["cmap"]


def main(args=None):
    """Build tables from a MS VOLT project into an OTF font"""
    parser = argparse.ArgumentParser(
        description="Use fontTools to compile MS VOLT projects."
    )
    parser.add_argument(
        "input",
        metavar="INPUT",
        help="Path to the input font/VTP file to process",
        type=Path,
    )
    parser.add_argument(
        "-f",
        "--font",
        metavar="INPUT_FONT",
        help="Path to the input font (if INPUT is a VTP file)",
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        metavar="OUTPUT",
        help="Path to the output font.",
        type=Path,
    )
    parser.add_argument(
        "-t",
        "--tables",
        metavar="TABLE_TAG",
        choices=SUPPORTED_TABLES,
        nargs="+",
        help="Specify the table(s) to be built.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase the logger verbosity. Multiple -v options are allowed.",
        action="count",
        default=0,
    )
    parser.add_argument(
        "-F",
        "--debug-feature-file",
        help="Write the generated feature file to disk.",
        action="store_true",
    )
    parser.add_argument(
        "-T",
        "--traceback",
        help="show traceback for exceptions.",
        action="store_true",
    )
    options = parser.parse_args(args)

    levels = ["WARNING", "INFO", "DEBUG"]
    configLogger(level=levels[min(len(levels) - 1, options.verbose)])

    output_font = options.output or Path(
        makeOutputFileName(options.font or options.input)
    )
    log.info(f"Compiling MS VOLT to '{output_font}'")

    file_or_path = options.input
    font = None

    # If the input is a font file, extract the VOLT data from the "TSIV" table
    try:
        font = TTFont(file_or_path)
        if "TSIV" in font:
            file_or_path = StringIO(font["TSIV"].data.decode("utf-8"))
        else:
            log.error('"TSIV" table is missing, font was not saved from VOLT?')
            return 1
    except TTLibError:
        pass

    # If input is not a font file, the font must be provided
    if font is None:
        if not options.font:
            log.error("Please provide an input font")
            return 1
        font = TTFont(options.font)

    doc = Parser(file_or_path).parse()

    converter = VoltToFea(doc, font)
    try:
        fea = converter.convert(options.tables, ignore_unsupported_settings=True)
    except NotImplementedError as e:
        if options.traceback:
            raise
        location = getattr(e.args[0], "location", None)
        message = f'"{e}" is not supported'
        if location:
            path, line, column = location
            log.error(f"{path}:{line}:{column}: {message}")
        else:
            log.error(message)
        return 1

    fea_filename = options.input
    if options.debug_feature_file:
        fea_filename = output_font.with_suffix(".fea")
        log.info(f"Writing feature file to '{fea_filename}'")
        with open(fea_filename, "w") as fp:
            fp.write(fea)

    try:
        addOpenTypeFeaturesFromString(
            font,
            fea,
            filename=fea_filename,
            tables=options.tables,
        )
    except FeatureLibError as e:
        if options.traceback:
            raise
        log.error(e)
        return 1

    if "TSIV" in font:
        del font["TSIV"]
    font.save(output_font)


if __name__ == "__main__":
    sys.exit(main())
