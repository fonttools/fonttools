"""
Tool to find wrong contour order between different masters, and
other interpolatability (or lack thereof) issues.

Call as:
$ fonttools varLib.interpolatable font1 font2 ...
"""

from ._interpolatable import test
from collections import defaultdict


def recursivelyAddGlyph(glyphname, glyphset, ttGlyphSet, glyf):
    if glyphname in glyphset:
        return
    glyphset[glyphname] = ttGlyphSet[glyphname]

    for component in getattr(glyf[glyphname], "components", []):
        recursivelyAddGlyph(component.glyphName, glyphset, ttGlyphSet, glyf)


def main(args=None):
    """Test for interpolatability issues between fonts"""
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.interpolatable",
        description=main.__doc__,
    )
    parser.add_argument(
        "--glyphs",
        action="store",
        help="Space-separate name of glyphs to check",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only exit with code 1 or 0, no output",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Will not report glyphs missing from sparse masters as errors",
    )
    parser.add_argument(
        "inputs",
        metavar="FILE",
        type=str,
        nargs="+",
        help="Input a single DesignSpace/Glyphs file, or multiple TTF/UFO files",
    )

    args = parser.parse_args(args)

    glyphs = args.glyphs.split() if args.glyphs else None

    from os.path import basename

    fonts = []
    names = []

    if len(args.inputs) == 1:
        if args.inputs[0].endswith(".designspace"):
            from fontTools.designspaceLib import DesignSpaceDocument

            designspace = DesignSpaceDocument.fromfile(args.inputs[0])
            args.inputs = [master.path for master in designspace.sources]

        elif args.inputs[0].endswith(".glyphs"):
            from glyphsLib import GSFont, to_ufos

            gsfont = GSFont(args.inputs[0])
            fonts.extend(to_ufos(gsfont))
            names = ["%s-%s" % (f.info.familyName, f.info.styleName) for f in fonts]
            args.inputs = []

        elif args.inputs[0].endswith(".ttf"):
            from fontTools.ttLib import TTFont

            font = TTFont(args.inputs[0])
            if "gvar" in font:
                # Is variable font
                gvar = font["gvar"]
                glyf = font["glyf"]
                # Gather all glyphs at their "master" locations
                ttGlyphSets = {}
                glyphsets = defaultdict(dict)

                if glyphs is None:
                    glyphs = sorted(gvar.variations.keys())
                for glyphname in glyphs:
                    for var in gvar.variations[glyphname]:
                        locDict = {}
                        loc = []
                        for tag, val in sorted(var.axes.items()):
                            locDict[tag] = val[1]
                            loc.append((tag, val[1]))

                        locTuple = tuple(loc)
                        if locTuple not in ttGlyphSets:
                            ttGlyphSets[locTuple] = font.getGlyphSet(
                                location=locDict, normalized=True
                            )

                        recursivelyAddGlyph(
                            glyphname, glyphsets[locTuple], ttGlyphSets[locTuple], glyf
                        )

                names = ["()"]
                fonts = [font.getGlyphSet()]
                for locTuple in sorted(glyphsets.keys(), key=lambda v: (len(v), v)):
                    names.append(str(locTuple))
                    fonts.append(glyphsets[locTuple])
                args.ignore_missing = True
                args.inputs = []

    for filename in args.inputs:
        if filename.endswith(".ufo"):
            from fontTools.ufoLib import UFOReader

            fonts.append(UFOReader(filename))
        else:
            from fontTools.ttLib import TTFont

            fonts.append(TTFont(filename))

        names.append(basename(filename).rsplit(".", 1)[0])

    glyphsets = []
    for font in fonts:
        if hasattr(font, "getGlyphSet"):
            glyphset = font.getGlyphSet()
        else:
            glyphset = font
        glyphsets.append({k: glyphset[k] for k in glyphset.keys()})

    if not glyphs:
        glyphs = sorted(set([gn for glyphset in glyphsets for gn in glyphset.keys()]))

    glyphsSet = set(glyphs)
    for glyphset in glyphsets:
        glyphSetGlyphNames = set(glyphset.keys())
        diff = glyphsSet - glyphSetGlyphNames
        if diff:
            for gn in diff:
                glyphset[gn] = None

    problems = test(
        glyphsets, glyphs=glyphs, names=names, ignore_missing=args.ignore_missing
    )

    if not args.quiet:
        if args.json:
            import json

            print(json.dumps(problems))
        else:
            for glyph, glyph_problems in problems.items():
                print(f"Glyph {glyph} was not compatible: ")
                for p in glyph_problems:
                    if p["type"] == "missing":
                        print("    Glyph was missing in master %s" % p["master"])
                    if p["type"] == "open_path":
                        print("    Glyph has an open path in master %s" % p["master"])
                    if p["type"] == "path_count":
                        print(
                            "    Path count differs: %i in %s, %i in %s"
                            % (p["value_1"], p["master_1"], p["value_2"], p["master_2"])
                        )
                    if p["type"] == "node_count":
                        print(
                            "    Node count differs in path %i: %i in %s, %i in %s"
                            % (
                                p["path"],
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            )
                        )
                    if p["type"] == "node_incompatibility":
                        print(
                            "    Node %o incompatible in path %i: %s in %s, %s in %s"
                            % (
                                p["node"],
                                p["path"],
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            )
                        )
                    if p["type"] == "contour_order":
                        print(
                            "    Contour order differs: %s in %s, %s in %s"
                            % (
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            )
                        )
                    if p["type"] == "wrong_start_point":
                        print(
                            "    Contour %d start point differs: %s, %s"
                            % (
                                p["contour"],
                                p["master_1"],
                                p["master_2"],
                            )
                        )
                    if p["type"] == "math_error":
                        print(
                            "    Miscellaneous error in %s: %s"
                            % (
                                p["master"],
                                p["error"],
                            )
                        )
    if problems:
        return problems


if __name__ == "__main__":
    import sys

    problems = main()
    sys.exit(int(bool(problems)))
