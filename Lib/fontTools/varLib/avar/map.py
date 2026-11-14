from fontTools.varLib.models import normalizeValue
from fontTools.varLib.models import piecewiseLinearMap
from fontTools.varLib.varStore import VarStoreInstancer
from fontTools.misc.fixedTools import floatToFixed, fixedToFloat
from fontTools.misc.roundTools import otRound


def _denormalize(v, triplet):
    if v >= 0:
        return triplet[1] + v * (triplet[2] - triplet[1])
    else:
        return triplet[1] + v * (triplet[1] - triplet[0])


def _load_font(parser, fontpath):
    """Load a variable font, or build one from a designspace, for a CLI."""
    from fontTools.ttLib import TTFont

    if fontpath.endswith(".designspace"):
        from .build import build

        font = TTFont()
        build(font, fontpath)
        return font
    font = TTFont(fontpath)
    if "fvar" not in font:
        parser.error(f"Font '{fontpath}' does not contain an 'fvar' table.")
    return font


def _parse_coordinates(parser, items, allow_default=False):
    """Parse ``AXIS=value`` CLI items into a location dict (shared by the CLIs).

    With ``allow_default``, a bare ``AXIS`` maps to ``None`` (the axis default).
    """
    location = {}
    for item in items:
        tag, sep, value = item.partition("=")
        if allow_default and tag and not sep:
            location[tag] = None
            continue
        if not sep or not tag or not value:
            parser.error(
                f"Invalid coordinate {item!r}. Expected AXIS=value, e.g. wght=500"
            )
        try:
            location[tag] = float(value)
        except ValueError:
            parser.error(
                f"Invalid coordinate value in {item!r}. Expected a number after '='"
            )
    return location


class ForwardMapper:
    """Prepare a font's axis mappings for repeated forward evaluations.

    map() accepts the same location and unit options as the module-level
    map() function. Axis metadata, segment maps, delta-set indices, and the
    VarStore evaluator are prepared once; the evaluator retains its region
    support cache between locations. No NumPy or SciPy dependency is needed.

    The font must contain fvar. Construct a new mapper after changing its
    fvar or avar tables.
    """

    def __init__(self, font):
        if "fvar" not in font:
            raise ValueError("Font does not contain an 'fvar' table")
        self.axes = tuple(font["fvar"].axes)
        self.triples = {
            a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in self.axes
        }
        self.tags = tuple(self.triples)
        avar = font.get("avar")
        self.version = getattr(avar, "majorVersion", 1)
        if self.version not in (1, 2):
            raise NotImplementedError("Unknown avar table version")
        self.segments = (
            {tag: dict(mapping) for tag, mapping in avar.segments.items()}
            if avar is not None
            else {}
        )
        self._instancer = None
        self._indices = ()
        if self.version == 2:
            index_map = avar.table.VarIdxMap
            self._indices = tuple(
                index_map[i] if index_map is not None else i
                for i in range(len(self.axes))
            )
            store = avar.table.VarStore
            if store is not None:
                self._instancer = VarStoreInstancer(store, self.axes)

    def map(
        self,
        location,
        *,
        inputNormalized=False,
        outputNormalized=False,
        dropZeroes=False,
    ):
        """Map a location, retaining prepared state for the next evaluation."""
        unknown_axes = sorted(location.keys() - self.triples.keys())
        if unknown_axes:
            raise ValueError(f"Unknown axis tag(s): {', '.join(unknown_axes)}")
        normalized = {
            tag: (
                location.get(tag, 0)
                if inputNormalized
                else normalizeValue(location.get(tag, triple[1]), triple)
            )
            for tag, triple in self.triples.items()
        }
        mapped = {
            tag: piecewiseLinearMap(value, self.segments.get(tag, {}))
            for tag, value in normalized.items()
        }
        if self.version == 2:
            instancer = self._instancer
            if instancer is not None:
                # Only the scalar cache is location-dependent. Keep the
                # compiled region supports across evaluations.
                instancer.setLocation(mapped)
            output = {}
            for tag, index in zip(self.tags, self._indices):
                value = floatToFixed(mapped[tag], 14)
                if instancer is not None:
                    value += otRound(instancer[index])
                    value = min(max(value, -16384), 16384)
                output[tag] = fixedToFloat(value, 14)
            mapped = output
        # Filtering happens in normalized space: zero can correspond to a
        # nonzero default when converted back to pre-fvar units.
        if dropZeroes:
            mapped = {tag: value for tag, value in mapped.items() if value != 0}
        if not outputNormalized:
            mapped = {
                tag: _denormalize(value, self.triples[tag])
                for tag, value in mapped.items()
            }
        return mapped


def map(
    font,
    location,
    *,
    inputNormalized=False,
    outputNormalized=False,
    dropZeroes=False,
    reverse=False,
    pinned=None,
    vary=None,
):
    """Map coordinates through avar, or approximately invert it.

    Omitted axes use their fvar defaults in user coordinates, or zero when
    inputNormalized is True. dropZeroes omits normalized-zero OUTPUT axes,
    independently of the input/output units and the avar version.

    With ``reverse=True``, return the ``(location, error)`` tuple from
    :func:`fontTools.varLib.avar.reverse.reverse`; otherwise return the mapped
    location. ``pinned`` and ``vary`` are only supported for reverse mapping.
    For repeated forward evaluations use ForwardMapper to reuse prepared state.
    """
    if reverse:
        from .reverse import reverse as reverse_map

        return reverse_map(
            font,
            location,
            inputNormalized=inputNormalized,
            outputNormalized=outputNormalized,
            dropZeroes=dropZeroes,
            pinned=pinned,
            vary=vary,
        )
    if pinned is not None:
        raise ValueError("Axis pins require reverse mapping")
    if vary is not None:
        raise ValueError("Axis vary lists require reverse mapping")
    if "fvar" not in font:
        return None

    return ForwardMapper(font).map(
        location,
        inputNormalized=inputNormalized,
        outputNormalized=outputNormalized,
        dropZeroes=dropZeroes,
    )


def main(args=None):
    """Map variation coordinates through the `avar` table."""

    import argparse
    import sys

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        "fonttools varLib.avar.map",
        description="Map variation coordinates through the `avar` table. "
        "To invert the mapping, see `fonttools varLib.avar.reverse`.",
    )
    parser.add_argument("font", metavar="varfont.ttf", help="Variable-font file.")
    parser.add_argument(
        "coords",
        metavar="[AXIS=value...]",
        help="Coordinates to map, e.g. 'wght=700 wdth=75'. "
        "Omit coordinates to map the default location.",
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "-f", action="store_true", help="Do not omit axes at default location."
    )
    parser.add_argument(
        "-i", action="store_true", help="Input coordinates are normalized (-1..1)."
    )
    parser.add_argument(
        "-o", action="store_true", help="Output coordinates as normalized (-1..1)."
    )

    options = parser.parse_args(args)

    font = _load_font(parser, options.font)
    location = _parse_coordinates(parser, options.coords)

    try:
        mapped = map(
            font,
            location,
            inputNormalized=options.i,
            outputNormalized=options.o,
            dropZeroes=not options.f,
        )
    except ValueError as e:
        parser.error(str(e))
    assert mapped is not None

    for tag in mapped:
        v = mapped[tag]
        v = int(v) if v == int(v) else v
        print(f"{tag}={v:g}")


if __name__ == "__main__":
    import sys

    sys.exit(main())
