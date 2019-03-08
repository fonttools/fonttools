""" Partially instantiate a variable font.

This is similar to fontTools.varLib.mutator, but instead of creating full
instances (i.e. static fonts) from variable fonts, it creates "partial"
variable fonts, only containing a subset of the variation space.
For example, if you wish to pin the width axis to a given location while
keeping the rest of the axes, you can do:

$ fonttools varLib.partialInstancer ./NotoSans-VF.ttf wdth=85

NOTE: The module is experimental and both the API and the CLI *will* change.
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import floatToFixedToFloat
from fontTools.varLib import _GetCoordinates, _SetCoordinates
from fontTools.varLib.models import supportScalar, normalizeValue, piecewiseLinearMap
from fontTools.varLib.iup import iup_delta
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
import logging
import os
import re


log = logging.getLogger("fontTools.varlib.partialInstancer")


def instantiateGvarGlyph(varfont, location, glyphname):
    gvar = varfont["gvar"]
    variations = gvar.variations[glyphname]
    coordinates, _ = _GetCoordinates(varfont, glyphname)
    origCoords, endPts = None, None
    newVariations = []
    pinnedAxes = set(location.keys())
    defaultModified = False
    for var in variations:
        tupleAxes = set(var.axes.keys())
        pinnedTupleAxes = tupleAxes & pinnedAxes
        if not pinnedTupleAxes:
            # A tuple for only axes being kept is untouched
            newVariations.append(var)
            continue
        else:
            # compute influence at pinned location only for the pinned axes
            pinnedAxesSupport = {a: var.axes[a] for a in pinnedTupleAxes}
            scalar = supportScalar(location, pinnedAxesSupport)
            if not scalar:
                # no influence (default value or out of range); drop tuple
                continue
            deltas = var.coordinates
            hasUntouchedPoints = None in deltas
            if hasUntouchedPoints:
                if origCoords is None:
                    origCoords, control = _GetCoordinates(varfont, glyphname)
                    numberOfContours = control[0]
                    isComposite = numberOfContours == -1
                    if isComposite:
                        endPts = list(range(len(control[1])))
                    else:
                        endPts = control[1]
                deltas = iup_delta(deltas, origCoords, endPts)
            scaledDeltas = GlyphCoordinates(deltas) * scalar
            if tupleAxes.issubset(pinnedAxes):
                # A tuple for only axes being pinned is discarded, and
                # it's contribution is reflected into the base outlines
                coordinates += scaledDeltas
                defaultModified = True
            else:
                # A tuple for some axes being pinned has to be adjusted
                var.coordinates = scaledDeltas
                for axis in pinnedTupleAxes:
                    del var.axes[axis]
                newVariations.append(var)
    if defaultModified:
        _SetCoordinates(varfont, glyphname, coordinates)
    gvar.variations[glyphname] = newVariations


def instantiateGvar(varfont, location):
    log.info("Instantiating glyf/gvar tables")

    gvar = varfont["gvar"]
    glyf = varfont["glyf"]
    # Get list of glyph names in gvar sorted by component depth.
    # If a composite glyph is processed before its base glyph, the bounds may
    # be calculated incorrectly because deltas haven't been applied to the
    # base glyph yet.
    glyphnames = sorted(
        gvar.variations.keys(),
        key=lambda name: (
            glyf[name].getCompositeMaxpValues(glyf).maxComponentDepth
            if glyf[name].isComposite()
            else 0,
            name,
        ),
    )
    for glyphname in glyphnames:
        instantiateGvarGlyph(varfont, location, glyphname)


def normalize(value, triple, avar_mapping):
    value = normalizeValue(value, triple)
    if avar_mapping:
        value = piecewiseLinearMap(value, avar_mapping)
    # Quantize to F2Dot14, to avoid surprise interpolations.
    return floatToFixedToFloat(value, 14)


def normalizeAxisLimits(varfont, axis_limits):
    fvar = varfont["fvar"]
    bad_limits = axis_limits.keys() - {a.axisTag for a in fvar.axes}
    if bad_limits:
        raise ValueError("Cannot limit: {} not present in fvar".format(bad_limits))

    axes = {
        a.axisTag: (a.minValue, a.defaultValue, a.maxValue)
        for a in fvar.axes
        if a.axisTag in axis_limits
    }

    avar_segments = {}
    if "avar" in varfont:
        avar_segments = varfont["avar"].segments
    for axis_tag, triple in axes.items():
        avar_mapping = avar_segments.get(axis_tag, None)
        axis_limits[axis_tag] = tuple(
            normalize(v, triple, avar_mapping) for v in axis_limits[axis_tag]
        )


def sanityCheckVariableTables(varfont):
    if "fvar" not in varfont:
        raise ValueError("Missing required table fvar")
    if "gvar" in varfont:
        if "glyf" not in varfont:
            raise ValueError("Can't have gvar without glyf")


def instantiateVariableFont(varfont, axis_limits, inplace=False):
    sanityCheckVariableTables(varfont)

    if not inplace:
        varfont = deepcopy(varfont)
    normalizeAxisLimits(varfont, axis_limits)

    log.info("Normalized limits: %s", axis_limits)

    if "gvar" in varfont:
        # TODO: support range, stop dropping max value
        axis_limits = {tag: minv for tag, (minv, maxv) in axis_limits.items()}
        print(axis_limits)
        instantiateGvar(varfont, axis_limits)

    # TODO: actually process HVAR instead of dropping it
    del varfont["HVAR"]

    return varfont


def parseLimits(limits):
    result = {}
    for limit_string in limits:
        match = re.match(r"^(\w{1,4})=([^:]+)(?:[:](.+))?$", limit_string)
        if not match:
            parser.error("invalid location format: %r" % limit_string)
        tag = match.group(1).ljust(4)
        lbound = float(match.group(2))
        ubound = lbound
        if match.group(3):
            ubound = float(match.group(3))
        result[tag] = (lbound, ubound)
    return result


def parseArgs(args):
    """Parse argv.

    Returns:
        3-tuple (infile, outfile, axis_limits)
        axis_limits is a map axis_tag:(min,max), meaning limit this axis to
        range."""
    from fontTools import configLogger
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.partialInstancer",
        description="Partially instantiate a variable font",
    )
    parser.add_argument("input", metavar="INPUT.ttf", help="Input variable TTF file.")
    parser.add_argument(
        "locargs",
        metavar="AXIS=LOC",
        nargs="*",
        help="List of space separated locations. A location consist in "
        "the name of a variation axis, followed by '=' and a number or"
        "number:number. E.g.: wdth=100 or wght=75.0:125.0",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT.ttf",
        default=None,
        help="Output instance TTF file (default: INPUT-instance.ttf).",
    )
    logging_group = parser.add_mutually_exclusive_group(required=False)
    logging_group.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )
    logging_group.add_argument(
        "-q", "--quiet", action="store_true", help="Turn verbosity off."
    )
    options = parser.parse_args(args)

    infile = options.input
    outfile = (
        os.path.splitext(infile)[0] + "-partial.ttf"
        if not options.output
        else options.output
    )
    configLogger(
        level=("DEBUG" if options.verbose else "ERROR" if options.quiet else "INFO")
    )

    axis_limits = parseLimits(options.locargs)
    if len(axis_limits) != len(options.locargs):
        raise ValueError("Specified multiple limits for the same axis")
    return (infile, outfile, axis_limits)


def main(args=None):
    infile, outfile, axis_limits = parseArgs(args)
    log.info("Restricting axes: %s", axis_limits)

    log.info("Loading variable font")
    varfont = TTFont(infile)

    instantiateVariableFont(varfont, axis_limits, inplace=True)

    log.info("Saving partial variable font %s", outfile)
    varfont.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
