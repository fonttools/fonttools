"""Convert between OpenType beyond-64k companion tables."""

from __future__ import annotations

import argparse
from collections.abc import Iterable

from fontTools.misc.cliTools import makeOutputFileName
from fontTools.ttLib import TTFont, TTLibError, newTable


_TABLE_PAIRS = {
    "glyf": "GLYF",
    "loca": "LOCA",
    "maxp": "MAXP",
    "hhea": "HHEA",
    "hmtx": "HMTX",
    "vhea": "VHEA",
    "vmtx": "VMTX",
    "gvar": "GVAR",
}
_UPPER_TABLES = _TABLE_PAIRS
_LOWER_TABLES = {upper: lower for lower, upper in _TABLE_PAIRS.items()}
_TABLE_IDENTITIES = {
    tag: lower for lower, upper in _TABLE_PAIRS.items() for tag in (lower, upper)
}


def _normalize_tables(tables: Iterable[str] | None) -> set[str]:
    if tables is None:
        return set(_TABLE_PAIRS)

    normalized = set()
    for tag in tables:
        try:
            normalized.add(_TABLE_IDENTITIES[tag])
        except KeyError:
            raise ValueError(f"Unsupported beyond-64k table: {tag!r}") from None
    return normalized


def _validate_family(font: TTFont) -> None:
    lower = sorted(tag for tag in _TABLE_PAIRS if tag in font)
    upper = sorted(tag for tag in _TABLE_PAIRS.values() if tag in font)
    if lower and upper:
        raise ValueError(
            "Mixed beyond-64k table family: "
            f"lowercase {', '.join(lower)}; uppercase {', '.join(upper)}"
        )


def _validate_lowering(font: TTFont, conversions: dict[str, str]) -> None:
    if "MAXP" in conversions and "MAXP" in font and font["MAXP"].numGlyphs > 0xFFFF:
        raise ValueError("MAXP.numGlyphs does not fit in maxp")
    if "HHEA" in conversions and "HHEA" in font:
        if font["HHEA"].numberOfHMetrics > 0xFFFF:
            raise ValueError("HHEA.numberOfHMetrics does not fit in hhea")
    if "VHEA" in conversions and "VHEA" in font:
        if font["VHEA"].numberOfVMetrics > 0xFFFF:
            raise ValueError("VHEA.numberOfVMetrics does not fit in vhea")


def _convert_table(font: TTFont, source, source_tag: str, destination_tag: str) -> None:
    destination = newTable(destination_tag)
    table_tag = destination.tableTag
    destination.__dict__.update(source.__dict__)
    destination.tableTag = table_tag
    font[destination_tag] = destination
    del font[source_tag]


def _convert_tables(
    font: TTFont,
    *,
    tables: Iterable[str] | None,
    table_conversions: dict[str, str],
    validate: bool,
    overwrite: bool,
    ignore_missing: bool,
    validate_conversion=None,
) -> None:
    tables = _normalize_tables(tables)
    conversions = {
        source: destination
        for source, destination in table_conversions.items()
        if _TABLE_IDENTITIES[source] in tables
    }
    if validate_conversion is not None:
        validate_conversion(font, conversions)

    pending = []
    for source_tag, destination_tag in conversions.items():
        source_exists = source_tag in font
        destination_exists = destination_tag in font

        if source_exists and destination_exists and not overwrite:
            raise ValueError(
                f"Both {source_tag!r} and {destination_tag!r} exist; "
                "set overwrite=True to replace the destination"
            )
        if not source_exists:
            if destination_exists or ignore_missing:
                continue
            raise KeyError(source_tag)
        pending.append((source_tag, destination_tag))

    if validate:
        result_tags = set(font.keys())
        for source_tag, destination_tag in pending:
            result_tags.discard(source_tag)
            result_tags.add(destination_tag)
        lower = sorted(tag for tag in _TABLE_PAIRS if tag in result_tags)
        upper = sorted(tag for tag in _TABLE_PAIRS.values() if tag in result_tags)
        if lower and upper:
            raise ValueError(
                "Conversion would create a mixed beyond-64k table family: "
                f"lowercase {', '.join(lower)}; uppercase {', '.join(upper)}"
            )

    sources = {source_tag: font[source_tag] for source_tag, _ in pending}
    for source_tag, destination_tag in pending:
        _convert_table(font, sources[source_tag], source_tag, destination_tag)

    if validate:
        _validate_family(font)


def upper_tables(
    font: TTFont,
    *,
    tables: Iterable[str] | None = None,
    validate: bool = True,
    overwrite: bool = False,
    ignore_missing: bool = True,
) -> None:
    """Convert selected tables to their beyond-64k companion forms."""
    _convert_tables(
        font,
        tables=tables,
        table_conversions=_UPPER_TABLES,
        validate=validate,
        overwrite=overwrite,
        ignore_missing=ignore_missing,
    )


def lower_tables(
    font: TTFont,
    *,
    tables: Iterable[str] | None = None,
    validate: bool = True,
    overwrite: bool = False,
    ignore_missing: bool = True,
) -> None:
    """Convert selected tables from their beyond-64k companion forms."""
    _convert_tables(
        font,
        tables=tables,
        table_conversions=_LOWER_TABLES,
        validate=validate,
        overwrite=overwrite,
        ignore_missing=ignore_missing,
        validate_conversion=_validate_lowering,
    )


def main(args=None):
    parser = argparse.ArgumentParser(
        "fonttools ttLib.beyond64k",
        description="Convert between OpenType beyond-64k companion tables",
    )
    parser.add_argument("direction", choices=("upper", "lower"))
    parser.add_argument("input", metavar="INPUT")
    parser.add_argument("tables", metavar="TABLE", nargs="*")
    parser.add_argument("-o", "--output", metavar="OUTPUT")
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--no-ignore-missing", dest="ignore_missing", action="store_false"
    )
    options = parser.parse_args(args)

    output = options.output or makeOutputFileName(
        options.input, overWrite=True, suffix=f"-{options.direction}"
    )
    with TTFont(options.input) as font:
        convert = upper_tables if options.direction == "upper" else lower_tables
        try:
            convert(
                font,
                tables=options.tables or None,
                validate=not options.no_validate,
                overwrite=options.overwrite,
                ignore_missing=options.ignore_missing,
            )
        except (KeyError, ValueError) as error:
            raise TTLibError(str(error)) from error
        font.save(output)


if __name__ == "__main__":
    main()
