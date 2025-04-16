__doc__ = """
Convert TrueType flavored fonts to CFF flavored fonts.

INPUT_PATH argument can be a file or a directory. If it is a directory, all the TrueType
flavored fonts found in the directory will be converted.

Examples:

    $ ttf2otf font.ttf
    $ ttf2otf font.ttf -o output_dir
    $ ttf2otf fonts_dir
    $ ttf2otf fonts_dir -r
    $ ttf2otf fonts_dir -o output_dir
    $ ttf2otf fonts_dir -o output_dir --no-overwrite
    $ ttf2otf fonts_dir -o output_dir --max-err 0.5
    $ ttf2otf fonts_dir -o output_dir --new-upem 1000
    $ ttf2otf fonts_dir -o output_dir --correct-contours
"""

import argparse
import logging
import sys
import typing as t
from pathlib import Path

import pathops
from cffsubr import subroutinize as subr
from fontTools import configLogger
from fontTools.cffLib import PrivateDict
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.cliTools import makeOutputFileName
from fontTools.misc.psCharStrings import T2CharString
from fontTools.misc.roundTools import otRound
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, TTLibError
from fontTools.ttLib.scaleUpem import scale_upem

log = logging.getLogger(__name__)


def decomponentize_tt(font: TTFont) -> None:
    """
    Decomposes all composite glyphs of a TrueType font.
    """
    if not font.sfntVersion == "\x00\x01\x00\x00":
        raise NotImplementedError(
            "Decomponentization is only supported for TrueType fonts."
        )

    glyph_set = font.getGlyphSet()
    glyf_table = font["glyf"]
    dr_pen = DecomposingRecordingPen(glyphSet=glyph_set)
    tt_pen = TTGlyphPen(glyphSet=None)

    for glyph_name in font.glyphOrder:
        glyph = glyf_table[glyph_name]
        if not glyph.isComposite():
            continue
        dr_pen.value = []
        tt_pen.init()
        glyph.draw(dr_pen, glyf_table)
        dr_pen.replay(tt_pen)
        glyf_table[glyph_name] = tt_pen.glyph()


def skia_path_from_charstring(charstring: T2CharString) -> pathops.Path:
    """
    Get a Skia path from a T2CharString.
    """
    path = pathops.Path()
    path_pen = path.getPen(glyphSet=None)
    charstring.draw(path_pen)
    return path


def charstring_from_skia_path(path: pathops.Path, width: int) -> T2CharString:
    """
    Get a T2CharString from a Skia path.
    """
    t2_pen = T2CharStringPen(width=width, glyphSet=None)
    path.draw(t2_pen)
    return t2_pen.getCharString()


def round_path(
    path: pathops.Path, rounder: t.Callable[[float], float] = otRound
) -> pathops.Path:
    """
    Rounds the points coordinate of a ``pathops.Path``

    Args:
        path (pathops.Path): The ``pathops.Path``
        rounder (Callable[[float], float], optional): The rounding function. Defaults to otRound.

    Returns:
        pathops.Path: The rounded path
    """

    rounded_path = pathops.Path()
    for verb, points in path:
        rounded_path.add(verb, *((rounder(p[0]), rounder(p[1])) for p in points))
    return rounded_path


def simplify_path(path: pathops.Path, glyph_name: str, clockwise: bool) -> pathops.Path:
    """
    Simplify a ``pathops.Path by`` removing overlaps, fixing contours direction and, optionally,
    removing tiny paths

    Args:
        path (pathops.Path): The ``pathops.Path`` to simplify
        glyph_name (str): The glyph name
        clockwise (bool): The winding direction. Must be ``True`` for TrueType glyphs and ``False``
            for OpenType-PS fonts.

    Returns:
        pathops.Path: The simplified path
    """

    try:
        return pathops.simplify(path, fix_winding=True, clockwise=clockwise)
    except pathops.PathOpsError:
        pass

    path = round_path(path)
    try:
        path = pathops.simplify(path, fix_winding=True, clockwise=clockwise)
        return path
    except pathops.PathOpsError as e:
        raise pathops.PathOpsError(
            f"Failed to simplify path for glyph {glyph_name}: {e}"
        )


def quadratics_to_cubics(
    font: TTFont, tolerance: float = 1.0, correct_contours: bool = False
) -> t.Dict[str, T2CharString]:
    """
    Get CFF charstrings using Qu2CuPen

    Args:
        font (TTFont): The TTFont object.
        tolerance (float, optional): The tolerance for the conversion. Defaults to 1.0.
        correct_contours (bool, optional): Whether to correct the contours with pathops. Defaults to
            False.

    Returns:
        tuple: A tuple containing the list of failed glyphs and the T2 charstrings.
    """

    qu2cu_charstrings = {}
    glyph_set = font.getGlyphSet()

    for k, v in glyph_set.items():
        width = v.width

        try:
            t2_pen = T2CharStringPen(width=width, glyphSet={k: v})
            qu2cu_pen = Qu2CuPen(
                t2_pen, max_err=tolerance, all_cubic=True, reverse_direction=True
            )
            glyph_set[k].draw(qu2cu_pen)
            qu2cu_charstrings[k] = t2_pen.getCharString()

        except NotImplementedError:
            # Workaround for "oncurve-less contours with all_cubic not implemented"
            temp_t2_pen = T2CharStringPen(width=width, glyphSet=None)
            glyph_set[k].draw(temp_t2_pen)
            t2_charstring = temp_t2_pen.getCharString()
            t2_charstring.private = PrivateDict()

            tt_pen = TTGlyphPen(glyphSet=None)
            cu2qu_pen = Cu2QuPen(
                other_pen=tt_pen, max_err=tolerance, reverse_direction=False
            )
            t2_charstring.draw(cu2qu_pen)
            tt_glyph = tt_pen.glyph()

            t2_pen = T2CharStringPen(width=width, glyphSet=None)
            qu2cu_pen = Qu2CuPen(
                t2_pen, max_err=tolerance, all_cubic=True, reverse_direction=True
            )
            tt_glyph.draw(pen=qu2cu_pen, glyfTable=None)
            log.warning(
                f"Failed to convert glyph '{k}' to cubic at first attempt, but succeeded at second "
                f"one."
            )

        charstring = t2_pen.getCharString()

        if correct_contours:
            charstring.private = PrivateDict()
            path = skia_path_from_charstring(charstring)
            simplified_path = simplify_path(path, glyph_name=k, clockwise=False)
            charstring = charstring_from_skia_path(path=simplified_path, width=width)

        qu2cu_charstrings[k] = charstring

    return qu2cu_charstrings


def build_font_info_dict(font: TTFont) -> t.Dict[str, t.Any]:
    """
    Builds CFF topDict from a TTFont object.

    Args:
        font (TTFont): The TTFont object.

    Returns:
        dict: The CFF topDict.
    """

    font_revision = str(round(font["head"].fontRevision, 3)).split(".")
    major_version = str(font_revision[0])
    minor_version = str(font_revision[1]).ljust(3, "0")

    name_table = font["name"]
    post_table = font["post"]
    cff_font_info = {
        "version": ".".join([major_version, str(int(minor_version))]),
        "FullName": name_table.getBestFullName(),
        "FamilyName": name_table.getBestFamilyName(),
        "ItalicAngle": post_table.italicAngle,
        "UnderlinePosition": post_table.underlinePosition,
        "UnderlineThickness": post_table.underlineThickness,
        "isFixedPitch": bool(post_table.isFixedPitch),
    }

    return cff_font_info


def get_post_values(font: TTFont) -> t.Dict[str, t.Any]:
    """
    Setup CFF post table values

    Args:
        font (TTFont): The TTFont object.

    Returns:
        dict: The post table values.
    """
    post_table = font["post"]
    post_info = {
        "italicAngle": otRound(post_table.italicAngle),
        "underlinePosition": post_table.underlinePosition,
        "underlineThickness": post_table.underlineThickness,
        "isFixedPitch": post_table.isFixedPitch,
        "minMemType42": post_table.minMemType42,
        "maxMemType42": post_table.maxMemType42,
        "minMemType1": post_table.minMemType1,
        "maxMemType1": post_table.maxMemType1,
    }
    return post_info


def get_hmtx_values(
    font: TTFont, charstrings: t.Dict[str, T2CharString]
) -> t.Dict[str, t.Tuple[int, int]]:
    """
    Get the horizontal metrics for a font.

    Args:
        font (TTFont): The TTFont object.
        charstrings (dict): The charstrings dictionary.

    Returns:
        dict: The horizontal metrics.
    """
    glyph_set = font.getGlyphSet()
    advance_widths = {k: v.width for k, v in glyph_set.items()}
    lsb = {}
    for gn, cs in charstrings.items():
        lsb[gn] = cs.calcBounds(None)[0] if cs.calcBounds(None) is not None else 0
    metrics = {}
    for gn, advance_width in advance_widths.items():
        metrics[gn] = (advance_width, lsb[gn])
    return metrics


def build_otf(
    font: TTFont,
    charstrings_dict: t.Dict[str, T2CharString],
    ps_name: t.Optional[str] = None,
    font_info: t.Optional[t.Dict[str, t.Any]] = None,
    private_dict: t.Optional[t.Dict[str, t.Any]] = None,
) -> None:
    """
    Builds an OpenType font with FontBuilder.

    Args:
        font (TTFont): The TTFont object.
        charstrings_dict (dict): The charstrings dictionary.
        ps_name (str, optional): The PostScript name of the font. Defaults to None.
        font_info (dict, optional): The font info dictionary. Defaults to None.
        private_dict (dict, optional): The private dictionary. Defaults to None.
    """

    if not ps_name:
        ps_name = font["name"].getDebugName(6)
    if not font_info:
        font_info = build_font_info_dict(font=font)
    if not private_dict:
        private_dict = {}

    fb = FontBuilder(font=font)
    fb.isTTF = False
    ttf_tables = ["glyf", "cvt ", "loca", "fpgm", "prep", "gasp", "LTSH", "hdmx"]
    for table in ttf_tables:
        if table in font:
            del font[table]
    fb.setupGlyphOrder(font.getGlyphOrder())
    fb.setupCFF(
        psName=ps_name,
        charStringsDict=charstrings_dict,
        fontInfo=font_info,
        privateDict=private_dict,
    )
    metrics = get_hmtx_values(font=fb.font, charstrings=charstrings_dict)
    fb.setupHorizontalMetrics(metrics)
    fb.setupDummyDSIG()
    fb.setupMaxp()
    post_values = get_post_values(font=fb.font)
    fb.setupPost(**post_values)


def find_fonts(
    input_path: Path, recursive: bool = False, recalc_timestamp: bool = False
) -> t.List[TTFont]:
    """
    Returns a list of TTFont objects found in the input path.

    Args:
        input_path (Path): The input file or directory.
        recursive (bool): If input_path is a directory, search for fonts recursively in
            subdirectories.
        recalc_timestamp (bool): Weather to recalculate the font's timestamp on save.

    Returns:
        List[TTFont]: A list of TTFont objects.
    """

    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        if recursive:
            files = [x for x in input_path.rglob("*") if x.is_file()]
        else:
            files = [x for x in input_path.glob("*") if x.is_file()]
    else:
        raise ValueError("Input path must be a file or directory.")

    fonts = []
    for file in files:
        try:
            font = TTFont(file, recalcTimestamp=recalc_timestamp)
            # Filter out CFF and variable fonts
            if font.sfntVersion == "\x00\x01\x00\x00" and "fvar" not in font:
                fonts.append(font)
        except (TTLibError, PermissionError):
            pass
    return fonts


def main(args=None) -> None:
    """
    Convert TrueType flavored fonts to CFF flavored fonts.

    INPUT_PATH argument can be a file or a directory. If it is a directory, all the TrueType
    flavored fonts found in the directory will be converted.
    """

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="The input file or directory.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search for fonts recursively in subdirectories.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Specify a directory where the output files are to be saved.",
    )
    parser.add_argument(
        "--no-overwrite",
        dest="overwrite",
        action="store_false",
        help="Do not overwrite the output file if it already exists.",
    )
    parser.add_argument(
        "-rt",
        "--recalc-timestamp",
        action="store_true",
        help="Recalculate the font's modified timestamp on save.",
    )
    parser.add_argument(
        "--max-err",
        type=float,
        default=1.0,
        help="The maximum error allowed when converting the font to TrueType.",
    )
    parser.add_argument(
        "--new-upem",
        type=int,
        help="The target UPM to scale the font to.",
    )
    parser.add_argument(
        "--correct-contours",
        action="store_true",
        help="Correct contours with pathops.",
    )
    parser.add_argument(
        "--no-subroutinize",
        dest="subroutinize",
        action="store_false",
        help="Do not subroutinize the converted font.",
    )

    args = parser.parse_args(args)

    input_path = args.input_path
    recursive = args.recursive
    output_dir = args.output_dir
    overwrite = args.overwrite
    recalc_timestamp = args.recalc_timestamp
    max_err = args.max_err
    new_upem = args.new_upem
    correct_contours = args.correct_contours
    subroutinize = args.subroutinize

    fonts = find_fonts(
        input_path, recursive=recursive, recalc_timestamp=recalc_timestamp
    )
    if not fonts:
        log.error("No TrueType flavored fonts found.")
        return

    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True)

    for font in fonts:
        with font:
            if font.sfntVersion != "\x00\x01\x00\x00":
                log.error(f"Font {font.reader.file.name} is not a TrueType font.")
                continue
            in_file = font.reader.file.name
            log.info(f"Converting {in_file}...")

            log.info("Decomponentizing source font...")
            decomponentize_tt(font)

            if new_upem:
                log.info(f"Scaling UPM to {new_upem}...")
                scale_upem(font=font, new_upem=new_upem)

            log.info("Converting to OTF...")
            charstrings_dict = quadratics_to_cubics(
                font, tolerance=max_err, correct_contours=correct_contours
            )

            ps_name = font["name"].getDebugName(6)
            font_info = build_font_info_dict(font=font)
            private_dict: t.Dict[str, t.Any] = {}
            build_otf(font, charstrings_dict, ps_name, font_info, private_dict)

            os_2_table = font["OS/2"]
            os_2_table.recalcAvgCharWidth(ttFont=font)

            if subroutinize:
                flavor = font.flavor
                font.flavor = None
                log.info("Subroutinizing...")
                subr(otf=font)
                font.flavor = flavor

            out_file = makeOutputFileName(
                input=in_file,
                outputDir=output_dir,
                extension=".otf" if font.flavor is None else f".{font.flavor}",
                suffix=".otf" if font.flavor is not None else "",
                overWrite=overwrite,
            )
            font.save(out_file)
            log.info(f"File saved to {out_file}")
            print()


if __name__ == "__main__":
    configLogger(logger=log, level="INFO")
    sys.exit(main())
