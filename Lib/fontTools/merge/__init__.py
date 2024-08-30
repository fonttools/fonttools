# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod, Roozbeh Pournader

from fontTools import ttLib
import fontTools.merge.base
from fontTools.merge.cmap import (
    computeMegaGlyphOrder,
    computeMegaCmap,
    renameCFFCharStrings,
)
from fontTools.merge.layout import layoutPreMerge, layoutPostMerge
import fontTools.merge.tables
from fontTools.misc.loggingTools import Timer
from functools import reduce
import argparse
import os
import sys
import logging
from types import SimpleNamespace
from copy import deepcopy


log = logging.getLogger("fontTools.merge")
timer = Timer(logger=logging.getLogger(__name__ + ".timer"), level=logging.INFO)


class Merger(object):
    """Font merger.

    This class merges multiple files into a single OpenType font, taking into
    account complexities such as OpenType layout (``GSUB``/``GPOS``) tables and
    cross-font metrics (e.g. ``hhea.ascent`` is set to the maximum value across
    all the fonts).

    If multiple glyphs map to the same Unicode value, and the glyphs are considered
    sufficiently different (that is, they differ in any of paths, widths, or
    height), then subsequent glyphs are renamed and a lookup in the ``locl``
    feature will be created to disambiguate them. For example, if the arguments
    are an Arabic font and a Latin font and both contain a set of parentheses,
    the Latin glyphs will be renamed to ``parenleft#1`` and ``parenright#1``,
    and a lookup will be inserted into the to ``locl`` feature (creating it if
    necessary) under the ``latn`` script to substitute ``parenleft`` with
    ``parenleft#1`` etc.

    Restrictions:

    - All fonts must have the same units per em.
    - If duplicate glyph disambiguation takes place as described above then the
            fonts must have a ``GSUB`` table.

    Attributes:
            options: Currently unused.
    """

    def __init__(self, options=None):
        if not options:
            options = SimpleNamespace(**{
                "drop_tables": [],
                "font_files": []
            })

        assert hasattr(options, "drop_tables")
        assert hasattr(options, "font_files")

        self.options = options

    def _openFonts(self, fontfiles):
        fonts = [ttLib.TTFont(fontfile) for fontfile in fontfiles]
        for font, fontfile in zip(fonts, fontfiles):
            font._merger__fontfile = fontfile
            font._merger__name = font["name"].getDebugName(4)
        return fonts
    
    def openFonts(self, fontfiles):
        return self._openFonts(fontfiles)

    def merge(self, fontfiles):
        """Merges fonts together.

        Args:
                fontfiles: A list of file names to be merged

        Returns:
                A :class:`fontTools.ttLib.TTFont` object. Call the ``save`` method on
                this to write it out to an OTF file.
        """
        fonts = self._openFonts(fontfiles)
        return self.mergeTTFonts(fonts)
    
    def mergeTTFonts(self, ttfonts):
        """Merges fonts together.

        Args:
                ttfonts: A list of :class:`fontTools.ttLib.TTFont` objects to be merged

        Returns:
                A :class:`fontTools.ttLib.TTFont` object. Call the ``save`` method on
                this to write it out to an OTF file.
        """
        #
        # Settle on a mega glyph order.
        #
        glyphOrders = [list(font.getGlyphOrder()) for font in ttfonts]
        computeMegaGlyphOrder(self, glyphOrders)

        # Take first input file sfntVersion
        sfntVersion = ttfonts[0].sfntVersion

        # Reload fonts and set new glyph names on them.
        fonts = deepcopy(ttfonts)
        for font, glyphOrder in zip(fonts, glyphOrders):
            font.setGlyphOrder(glyphOrder)
            if "CFF " in font:
                renameCFFCharStrings(self, glyphOrder, font["CFF "])

        cmaps = [font["cmap"] for font in fonts]
        self.duplicateGlyphsPerFont = [{} for _ in fonts]
        computeMegaCmap(self, cmaps)

        mega = ttLib.TTFont(sfntVersion=sfntVersion)
        mega.setGlyphOrder(self.glyphOrder)

        for font in fonts:
            self._preMerge(font)

        self.fonts = fonts

        allTags = reduce(set.union, (list(font.keys()) for font in fonts), set())
        allTags.remove("GlyphOrder")

        for tag in sorted(allTags):
            if tag in self.options.drop_tables:
                continue

            with timer("merge '%s'" % tag):
                tables = [font.get(tag, NotImplemented) for font in fonts]

                log.info("Merging '%s'.", tag)
                clazz = ttLib.getTableClass(tag)
                table = clazz(tag).merge(self, tables)
                # XXX Clean this up and use:  table = mergeObjects(tables)

                if table is not NotImplemented and table is not False:
                    mega[tag] = table
                    log.info("Merged '%s'.", tag)
                else:
                    log.info("Dropped '%s'.", tag)

        del self.duplicateGlyphsPerFont
        del self.fonts

        self._postMerge(mega)

        return mega

    def mergeObjects(self, returnTable, logic, tables):
        # Right now we don't use self at all.  Will use in the future
        # for options and logging.

        allKeys = set.union(
            set(),
            *(vars(table).keys() for table in tables if table is not NotImplemented),
        )
        for key in allKeys:
            log.info(" %s", key)
            try:
                mergeLogic = logic[key]
            except KeyError:
                try:
                    mergeLogic = logic["*"]
                except KeyError:
                    raise Exception(
                        "Don't know how to merge key %s of class %s"
                        % (key, returnTable.__class__.__name__)
                    )
            if mergeLogic is NotImplemented:
                continue
            value = mergeLogic(getattr(table, key, NotImplemented) for table in tables)
            if value is not NotImplemented:
                setattr(returnTable, key, value)

        return returnTable

    def _preMerge(self, font):
        layoutPreMerge(font)

    def _postMerge(self, font):
        layoutPostMerge(font)

        if "OS/2" in font:
            # https://github.com/fonttools/fonttools/issues/2538
            # TODO: Add an option to disable this?
            font["OS/2"].recalcAvgCharWidth(font)


__all__ = ["Options", "Merger", "main"]

class SplitArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(','))

@timer("make one with everything (TOTAL TIME)")
def main(args=None):
    """Merge multiple fonts into one"""
    from fontTools import configLogger

    parser = argparse.ArgumentParser(
                    prog='pyftmerge',
                    description='Merge multiple fonts into one font',)
    
    parser.add_argument('font_files', metavar='font', type=str, nargs='*',
                        help='Files to merge')
    parser.add_argument('--input-file', type=str, help='Read font files to merge from a text file, each path new line. # Comment lines allowed.')
    parser.add_argument('--output-file', type=str, help='Specify output file name (default: merged.ttf)', default='merged.ttf')
    parser.add_argument('--import-file', type=str, help='TTX file to import after merging. This can be used to set metadata.')
    parser.add_argument('--drop-tables', type=str, action=SplitArgs, help='Comma separated list of table tags to skip, case sensitive.', default=[])
    parser.add_argument('--verbose', action='store_true', help='Output progress information.', default=False)
    parser.add_argument('--timing', action='store_true', help='Output progress timing.', default=False)

    args = parser.parse_args(args)

    # File validation
    if args.input_file is not None and not os.path.exists(args.input_file):
        parser.error(f"Input font lists '{args.input_file}' through --input-file does not exist")
    if args.import_file is not None and not os.path.exists(args.import_file):
        parser.error(f"TTX file to import '{args.import_file}' through --import-file does not exist")

    if args.input_file:
        with open(args.input_file) as inputfile:
            fontfiles = [
                line.strip()
                for line in inputfile.readlines()
                if not line.lstrip().startswith("#")
            ]
            args.font_files.extend(fontfiles)

    if len(args.font_files) < 1:
        parser.error('No font files specified through [font ...] or --input-file')

    configLogger(level=logging.INFO if args.verbose else logging.WARNING)
    if args.timing:
        timer.logger.setLevel(logging.DEBUG)
    else:
        timer.logger.disabled = True

    merger = Merger(options=args)
    font = merger.merge(args.font_files)

    if args.import_file:
        font.importXML(args.import_file)

    with timer("compile and save font"):
        font.save(args.output_file)


if __name__ == "__main__":
    sys.exit(main())
