"""Convert between Open Font Format beyond-64k companion tables.

The Open Font Format beyond-64k specification adds uppercase companion tables and
extended Layout formats that can address glyph IDs above 65535. This module
provides helpers to convert a :class:`fontTools.ttLib.TTFont` in place between
the compact lowercase table family and the extended uppercase table family.

The high-level APIs are :func:`upper_tables` and :func:`lower_tables`. By
default they convert every known table present in the font and validate that
the result does not mix lowercase and uppercase companion tables. Both helpers
accept an optional ``tables`` iterable; each entry may use either the compact or
extended spelling, e.g. ``"glyf"`` and ``"GLYF"`` both identify the glyph table
family.

The module is also available as a command-line tool::

    fonttools ttLib.beyond64k upper input.ttf -o upper.ttf
    fonttools ttLib.beyond64k lower upper.ttf -o lower.ttf
    fonttools ttLib.beyond64k upper input.ttf GSUB GPOS glyf

Lowering validates lossy cases such as ``MAXP.numGlyphs`` values above 65535,
``GLYF`` glyphs with cubic outlines, and component glyph IDs that do not fit in
the compact ``glyf`` table.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable

from fontTools.misc.cliTools import makeOutputFileName
from fontTools.ttLib import TTFont, TTLibError, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.otTraverse import dfs_base_table

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
_TABLE_IDENTITIES = {
    tag: lower for lower, upper in _TABLE_PAIRS.items() for tag in (lower, upper)
}
_TABLE_IDENTITIES.update(
    {
        "BASE": "BASE",
        "COLR": "COLR",
        "GDEF": "GDEF",
        "GPOS": "GPOS",
        "GSUB": "GSUB",
        "JSTF": "JSTF",
        "VORG": "VORG",
    }
)


@dataclass(frozen=True)
class _TableConversion:
    destination: str
    transform: Callable | None = None


_EXPLICIT_LAYOUT_FORMATS = {
    (otTables.BaseCoord, 2): (4, {}),
    (otTables.SinglePos, 1): (3, {}),
    (otTables.SinglePos, 2): (4, {}),
    (otTables.PairPos, 1): (
        3,
        {
            otTables.PairSet: otTables.PairSet2,
            otTables.PairValueRecord: otTables.PairValue2,
        },
    ),
    (otTables.PairPos, 2): (4, {}),
    (otTables.CursivePos, 1): (
        2,
        {otTables.EntryExitRecord: otTables.EntryExit2},
    ),
    (otTables.MarkBasePos, 1): (
        2,
        {
            otTables.MarkArray: otTables.MarkArray2,
            otTables.MarkRecord: otTables.MarkRecord2,
            otTables.BaseArray: otTables.BaseArray2,
            otTables.BaseRecord: otTables.BaseRecord2,
        },
    ),
    (otTables.MarkLigPos, 1): (
        2,
        {
            otTables.MarkArray: otTables.MarkArray2,
            otTables.MarkRecord: otTables.MarkRecord2,
            otTables.LigatureArray: otTables.LigatureArray2,
            otTables.LigatureAttach: otTables.LigatureAttach2,
            otTables.ComponentRecord: otTables.ComponentRecord2,
        },
    ),
    (otTables.MarkMarkPos, 1): (
        2,
        {
            otTables.MarkArray: otTables.MarkArray2,
            otTables.MarkRecord: otTables.MarkRecord2,
            otTables.Mark2Array: otTables.Mark2Array2,
            otTables.Mark2Record: otTables.Mark2Record2,
        },
    ),
    (otTables.ReverseChainSingleSubst, 1): (2, {}),
}


def _contextual_layout_conversion(
    table_type, compact_format, lookup_prefix, chaining=False
):
    compact_prefix = ("Chain" if chaining else "") + lookup_prefix[:3]
    class_based = compact_format == 2
    compact_rule = compact_prefix + ("ClassRule" if class_based else "Rule")
    compact_rule_set = compact_prefix + ("ClassSet" if class_based else "RuleSet")
    extended_rule = ("Chained" if chaining else "") + (
        "ClassSeqRule" if class_based else "SeqRule"
    )
    extended_rule_set = extended_rule + "Set"
    lookup_count = lookup_prefix + "Count"
    lookup_record = lookup_prefix + "LookupRecord"
    replacements = {getattr(otTables, lookup_record): (otTables.SeqLookup, {})}
    outer_renames = {
        lookup_count: "SeqLookupCount",
        lookup_record: "SeqLookupRecord",
    }

    if compact_format in (1, 2):
        replacements[getattr(otTables, compact_rule_set)] = (
            getattr(otTables, extended_rule_set + "2"),
            {
                compact_rule + "Count": extended_rule + "Count",
                compact_rule: extended_rule,
            },
        )
        rule_renames = {
            lookup_count: "SeqLookupCount",
            lookup_record: "SeqLookupRecord",
        }
        if chaining:
            rule_renames.update(
                {
                    "Backtrack": "BacktrackSequence",
                    "Input": "InputSequence",
                    "LookAhead": "LookAheadSequence",
                }
            )
        else:
            rule_renames["Class" if class_based else "Input"] = "InputSequence"
        replacements[getattr(otTables, compact_rule)] = (
            getattr(otTables, extended_rule + ("" if class_based else "2")),
            rule_renames,
        )
        outer_renames = {
            compact_rule_set + "Count": extended_rule_set + "Count",
            compact_rule_set: extended_rule_set,
        }

    return table_type, compact_format, compact_format + 3, outer_renames, replacements


_CONTEXTUAL_LAYOUT_FORMATS = {
    (table_type, compact_format): (extended_format, outer_renames, replacements)
    for (
        table_type,
        compact_format,
        extended_format,
        outer_renames,
        replacements,
    ) in (
        *(
            _contextual_layout_conversion(otTables.ContextSubst, format, "Subst")
            for format in (1, 2, 3)
        ),
        *(
            _contextual_layout_conversion(otTables.ContextPos, format, "Pos")
            for format in (1, 2, 3)
        ),
        *(
            _contextual_layout_conversion(
                otTables.ChainContextSubst, format, "Subst", chaining=True
            )
            for format in (1, 2)
        ),
        *(
            _contextual_layout_conversion(
                otTables.ChainContextPos, format, "Pos", chaining=True
            )
            for format in (1, 2)
        ),
    )
}


def _rename_layout_attributes(table, renames):
    for source, destination in renames.items():
        if hasattr(table, source):
            setattr(table, destination, getattr(table, source))
            delattr(table, source)


def _replace_layout_subtree(table, replacements):
    for path in reversed(list(dfs_base_table(table))):
        subtable = path[-1].value
        replacement_type, renames = replacements.get(
            type(subtable), (type(subtable), {})
        )
        _rename_layout_attributes(subtable, renames)
        if replacement_type is type(subtable):
            continue
        replacement = replacement_type()
        replacement.__dict__.update(subtable.__dict__)
        parent = path[-2].value
        entry = path[-1]
        if entry.index is None:
            setattr(parent, entry.name, replacement)
        else:
            getattr(parent, entry.name)[entry.index] = replacement


def _replace_layout_classes(table, replacements):
    for path in reversed(list(dfs_base_table(table))):
        subtable = path[-1].value
        replacement_type = replacements.get(type(subtable))
        if replacement_type is None:
            continue
        replacement = replacement_type()
        replacement.__dict__.update(subtable.__dict__)
        parent = path[-2].value
        entry = path[-1]
        if entry.index is None:
            setattr(parent, entry.name, replacement)
        else:
            getattr(parent, entry.name)[entry.index] = replacement


def _convert_contextual_layout_formats(table, extended):
    conversions = _CONTEXTUAL_LAYOUT_FORMATS
    if not extended:
        conversions = {
            (table_type, extended_format): (
                compact_format,
                {destination: source for source, destination in outer_renames.items()},
                {
                    extended_type: (
                        compact_type,
                        {
                            destination: source
                            for source, destination in renames.items()
                        },
                    )
                    for compact_type, (extended_type, renames) in replacements.items()
                },
            )
            for (table_type, compact_format), (
                extended_format,
                outer_renames,
                replacements,
            ) in conversions.items()
        }

    changed = False
    for path in dfs_base_table(table):
        subtable = path[-1].value
        conversion = conversions.get(
            (type(subtable), getattr(subtable, "Format", None))
        )
        if conversion is None:
            continue
        format, outer_renames, replacements = conversion
        _replace_layout_subtree(subtable, replacements)
        _rename_layout_attributes(subtable, outer_renames)
        subtable.Format = format
        changed = True
    return changed


def _convert_explicit_layout_formats(table, extended):
    conversions = _EXPLICIT_LAYOUT_FORMATS
    if not extended:
        conversions = {
            (table_type, extended_format): (
                compact_format,
                {extended: compact for compact, extended in replacements.items()},
            )
            for (table_type, compact_format), (
                extended_format,
                replacements,
            ) in conversions.items()
        }

    changed = False
    for path in dfs_base_table(table):
        subtable = path[-1].value
        conversion = conversions.get(
            (type(subtable), getattr(subtable, "Format", None))
        )
        if conversion is None:
            continue
        subtable.Format, replacements = conversion
        _replace_layout_classes(subtable, replacements)
        changed = True
    return changed


def _convert_layout_formats(table, extended):
    contextual = _convert_contextual_layout_formats(table, extended)
    explicit = _convert_explicit_layout_formats(table, extended)
    return contextual or explicit


def _convert_table_object(table, table_type):
    table.ensureDecompiled()
    converted = table_type()
    converted.__dict__.update(table.__dict__)
    return converted


def _move_fields(table, names, extended, overwrite):
    for name in names:
        compact_name = name
        extended_name = name + "2"
        source_name, destination_name = (
            (compact_name, extended_name) if extended else (extended_name, compact_name)
        )
        source = getattr(table, source_name, None)
        destination = getattr(table, destination_name, None)
        if source is not None and destination is not None and not overwrite:
            raise ValueError(
                f"Both {source_name!r} and {destination_name!r} exist; "
                "set overwrite=True to replace the destination"
            )
        if source is not None:
            setattr(table, destination_name, source)
            setattr(table, source_name, None)


def _upper_gdef(font, table, overwrite):
    table = table.table
    _move_fields(
        table,
        (
            "GlyphClassDef",
            "AttachList",
            "LigCaretList",
            "MarkAttachClassDef",
            "MarkGlyphSetsDef",
        ),
        True,
        overwrite,
    )
    if getattr(table, "LigCaretList2", None) is not None:
        table.LigCaretList2 = _convert_table_object(
            table.LigCaretList2, otTables.LigCaretList2
        )
    table.Version = max(table.Version, 0x00010004)
    _convert_layout_formats(table, True)


def _lower_gdef(font, table, overwrite):
    table = table.table
    _move_fields(
        table,
        (
            "GlyphClassDef",
            "AttachList",
            "LigCaretList",
            "MarkAttachClassDef",
            "MarkGlyphSetsDef",
        ),
        False,
        overwrite,
    )
    if getattr(table, "LigCaretList", None) is not None:
        table.LigCaretList = _convert_table_object(
            table.LigCaretList, otTables.LigCaretList
        )
    if getattr(table, "VarStore", None) is not None:
        table.Version = 0x00010003
    elif getattr(table, "MarkGlyphSetsDef", None) is not None:
        table.Version = 0x00010002
    else:
        table.Version = 0x00010000
    _convert_layout_formats(table, False)


def _upper_layout_formats(font, table, overwrite):
    _convert_layout_formats(table.table, True)


def _lower_layout_formats(font, table, overwrite):
    _convert_layout_formats(table.table, False)


def _upper_jstf(font, table, overwrite):
    table = table.table
    _replace_layout_subtree(
        table,
        {
            otTables.JstfScriptRecord: (otTables.JstfScriptRecord2, {}),
            otTables.JstfScript: (otTables.JstfScript2, {}),
            otTables.ExtenderGlyph: (otTables.ExtenderGlyph2, {}),
        },
    )
    _rename_layout_attributes(
        table,
        {
            "JstfScriptCount": "JstfScriptCount2",
            "JstfScriptRecord": "JstfScriptRecord2",
        },
    )
    table.Version = max(table.Version, 0x00010001)


def _lower_jstf(font, table, overwrite):
    table = table.table
    _replace_layout_subtree(
        table,
        {
            otTables.JstfScriptRecord2: (otTables.JstfScriptRecord, {}),
            otTables.JstfScript2: (otTables.JstfScript, {}),
            otTables.ExtenderGlyph2: (otTables.ExtenderGlyph, {}),
        },
    )
    _rename_layout_attributes(
        table,
        {
            "JstfScriptCount2": "JstfScriptCount",
            "JstfScriptRecord2": "JstfScriptRecord",
        },
    )
    table.Version = 0x00010000


def _upper_layout_header(font, table, overwrite):
    table = table.table
    _move_fields(table, ("ScriptList", "FeatureList", "LookupList"), True, overwrite)
    if getattr(table, "LookupList2", None) is not None:
        table.LookupList2 = _convert_table_object(
            table.LookupList2, otTables.LookupList2
        )
    table.Version = max(table.Version, 0x00010002)
    _convert_layout_formats(table, True)


def _lower_layout_header(font, table, overwrite):
    table = table.table
    _move_fields(table, ("ScriptList", "FeatureList", "LookupList"), False, overwrite)
    if getattr(table, "LookupList", None) is not None:
        table.LookupList = _convert_table_object(table.LookupList, otTables.LookupList)
    table.Version = (
        0x00010001 if getattr(table, "FeatureVariations", None) else 0x00010000
    )
    _convert_layout_formats(table, False)


def _has_extended_layout_formats(table):
    # The dispatch formats live on lookup subtables, including those wrapped
    # by extension lookups. Avoid descending through every rule/value record
    # merely to discover that an ordinary compact font needs no conversion.
    lookup_list = getattr(table, "LookupList", None)
    if lookup_list is None:
        return False
    extended_formats = {
        (table_type, conversion[0])
        for conversions in (_CONTEXTUAL_LAYOUT_FORMATS, _EXPLICIT_LAYOUT_FORMATS)
        for (table_type, _), conversion in conversions.items()
    }
    for lookup in lookup_list.Lookup:
        for subtable in lookup.SubTable:
            if isinstance(subtable, (otTables.ExtensionSubst, otTables.ExtensionPos)):
                subtable = subtable.ExtSubTable
            if (type(subtable), getattr(subtable, "Format", None)) in extended_formats:
                return True
    return False


@contextmanager
def _compact_layout_tables(font, *, restore=True):
    # Use compact in-memory layouts for algorithms that dispatch on them.
    # No compact serialization occurs here: glyph IDs and counts stay intact.
    restore_actions = []
    try:
        for tag, version, lower, upper in (
            ("GDEF", 0x00010004, _lower_gdef, _upper_gdef),
            ("GSUB", 0x00010002, _lower_layout_header, _upper_layout_header),
            ("GPOS", 0x00010002, _lower_layout_header, _upper_layout_header),
        ):
            if tag not in font:
                continue
            table = font[tag]
            if table.table.Version >= version:
                restore_actions.append((tag, upper))
                lower(font, table, True)
            elif _has_extended_layout_formats(table.table):
                _convert_layout_formats(table.table, False)
                restore_actions.append((tag, None))
        yield
    finally:
        for tag, upper in restore_actions if restore else ():
            if tag not in font:
                continue
            if upper is not None:
                upper(font, font[tag], True)
            else:
                _convert_layout_formats(font[tag].table, True)


def _lower_glyf(font, table, overwrite):
    from fontTools.ttLib.tables._g_l_y_f import flagCubic

    # Validation has rejected active or hinted CUBIC bits. Explicit lowering
    # may discard the remaining inert bits on unhinted on-curve points.
    for glyph_name in font.getGlyphOrder():
        glyph = table[glyph_name]
        if hasattr(glyph, "flags"):
            for i, flag in enumerate(glyph.flags):
                glyph.flags[i] = flag & ~flagCubic


def _upper_vorg(font, table, overwrite):
    table.majorVersion = 2
    table.minorVersion = 0


def _lower_vorg(font, table, overwrite):
    table.majorVersion = 1
    table.minorVersion = 0


def _iter_colr_paints(table):
    if not hasattr(table, "table"):
        return
    for path in dfs_base_table(table.table):
        value = path[-1].value
        if isinstance(value, otTables.Paint):
            yield value


def _upper_colr(font, table, overwrite):
    for paint in _iter_colr_paints(table):
        if paint.Format == otTables.PaintFormat.PaintGlyph:
            paint.Format = otTables.PaintFormat.PaintGlyph2


def _lower_colr(font, table, overwrite):
    for paint in _iter_colr_paints(table):
        if paint.Format == otTables.PaintFormat.PaintGlyph2:
            paint.Format = otTables.PaintFormat.PaintGlyph


_UPPER_TABLES = {
    **{
        source: _TableConversion(destination)
        for source, destination in _TABLE_PAIRS.items()
    },
    "BASE": _TableConversion("BASE", _upper_layout_formats),
    "COLR": _TableConversion("COLR", _upper_colr),
    "GDEF": _TableConversion("GDEF", _upper_gdef),
    "GSUB": _TableConversion("GSUB", _upper_layout_header),
    "GPOS": _TableConversion("GPOS", _upper_layout_header),
    "JSTF": _TableConversion("JSTF", _upper_jstf),
    "VORG": _TableConversion("VORG", _upper_vorg),
}
_LOWER_TABLES = {
    **{upper: _TableConversion(lower) for lower, upper in _TABLE_PAIRS.items()},
    "GLYF": _TableConversion("glyf", _lower_glyf),
    "BASE": _TableConversion("BASE", _lower_layout_formats),
    "COLR": _TableConversion("COLR", _lower_colr),
    "GDEF": _TableConversion("GDEF", _lower_gdef),
    "GSUB": _TableConversion("GSUB", _lower_layout_header),
    "GPOS": _TableConversion("GPOS", _lower_layout_header),
    "JSTF": _TableConversion("JSTF", _lower_jstf),
    "VORG": _TableConversion("VORG", _lower_vorg),
}


def _normalize_tables(tables: Iterable[str] | None) -> set[str]:
    if tables is None:
        return set(_TABLE_IDENTITIES.values())

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


def _validate_lowering(font: TTFont, conversions: dict[str, _TableConversion]) -> None:
    if "GLYF" in conversions and "GLYF" in font:
        from fontTools.ttLib.tables._g_l_y_f import flagCubic, flagOnCurve

        glyf = font["GLYF"]
        for glyph_name in font.getGlyphOrder():
            glyph = glyf[glyph_name]
            if glyph.isComposite():
                for component in glyph.components:
                    if font.getGlyphID(component.glyphName) > 0xFFFF:
                        raise ValueError(
                            f"GLYF component {component.glyphName!r} does not fit in glyf"
                        )
            else:
                cubic_flags = [
                    flag for flag in getattr(glyph, "flags", ()) if flag & flagCubic
                ]
                program = getattr(glyph, "program", None)
                # Hinting can flip an on-curve point and activate its CUBIC bit.
                if cubic_flags and (
                    any(not flag & flagOnCurve for flag in cubic_flags)
                    or (program and program.getBytecode())
                ):
                    raise ValueError(
                        f"GLYF glyph {glyph_name!r} has cubic outlines or hinted CUBIC flags"
                    )
    if "MAXP" in conversions and "MAXP" in font and font["MAXP"].numGlyphs > 0xFFFF:
        raise ValueError("MAXP.numGlyphs does not fit in maxp")
    if "HHEA" in conversions and "HHEA" in font:
        if font["HHEA"].numberOfHMetrics > 0xFFFF:
            raise ValueError("HHEA.numberOfHMetrics does not fit in hhea")
    if "VHEA" in conversions and "VHEA" in font:
        if font["VHEA"].numberOfVMetrics > 0xFFFF:
            raise ValueError("VHEA.numberOfVMetrics does not fit in vhea")
    if "VORG" in conversions and "VORG" in font:
        vorg = font["VORG"]
        if len(vorg.VOriginRecords) > 0xFFFF:
            raise ValueError("VORG record count does not fit in version 1")
        for glyph_name in vorg.VOriginRecords:
            if font.getGlyphID(glyph_name) > 0xFFFF:
                raise ValueError(f"VORG glyph {glyph_name!r} does not fit in version 1")
    if "COLR" in conversions and "COLR" in font:
        for paint in _iter_colr_paints(font["COLR"]):
            if (
                paint.Format == otTables.PaintFormat.PaintGlyph2
                and font.getGlyphID(paint.Glyph) > 0xFFFF
            ):
                raise ValueError(
                    f"COLR PaintGlyph2 glyph {paint.Glyph!r} does not fit in PaintGlyph"
                )
    _validate_cmap_uvs_lowering(font)


def _cmap_subtable_key(subtable) -> tuple[int, int, int]:
    return subtable.platformID, subtable.platEncID, subtable.language


def _merge_uvs_dict(destination, source) -> None:
    for selector, entries in source.items():
        merged = dict(destination.get(selector, ()))
        merged.update(entries)
        destination[selector] = sorted(merged.items())


def _copy_uvs_subtable(format: int, source):
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

    subtable = CmapSubtable.newSubtable(format)
    subtable.platformID = source.platformID
    subtable.platEncID = source.platEncID
    subtable.language = source.language
    subtable.cmap = {}
    subtable.uvsDict = {
        selector: list(entries) for selector, entries in source.uvsDict.items()
    }
    return subtable


def _uvs_has_high_glyph_id(font: TTFont, subtable) -> bool:
    subtable.ensureDecompiled()
    for entries in subtable.uvsDict.values():
        for _, glyph_name in entries:
            if glyph_name is not None and font.getGlyphID(glyph_name) > 0xFFFF:
                return True
    return False


def _character_map_tables(font: TTFont):
    for tag in ("cmap", "DMAP"):
        if tag in font:
            yield tag, font[tag]


def _validate_cmap_uvs_lowering(font: TTFont) -> None:
    for tag, character_map in _character_map_tables(font):
        for subtable in character_map.tables:
            if subtable.format == 15 and _uvs_has_high_glyph_id(font, subtable):
                raise ValueError(f"{tag} format 15 glyph IDs do not fit in format 14")


def _upper_beyond64k_cmap_uvs(font: TTFont) -> None:
    for _, character_map in _character_map_tables(font):
        format15_by_key = {
            _cmap_subtable_key(subtable): subtable
            for subtable in character_map.tables
            if subtable.format == 15
        }
        tables = []
        for subtable in character_map.tables:
            if subtable.format == 14 and _uvs_has_high_glyph_id(font, subtable):
                key = _cmap_subtable_key(subtable)
                format15 = format15_by_key.get(key)
                if format15 is None:
                    format15 = _copy_uvs_subtable(15, subtable)
                    format15_by_key[key] = format15
                    tables.append(format15)
                else:
                    format15.ensureDecompiled()
                    _merge_uvs_dict(format15.uvsDict, subtable.uvsDict)
                continue
            tables.append(subtable)
        character_map.tables = tables


def _lower_beyond64k_cmap_uvs(font: TTFont) -> None:
    for tag, character_map in _character_map_tables(font):
        format14_by_key = {
            _cmap_subtable_key(subtable): subtable
            for subtable in character_map.tables
            if subtable.format == 14
        }
        tables = []
        for subtable in character_map.tables:
            if subtable.format == 15:
                if _uvs_has_high_glyph_id(font, subtable):
                    raise ValueError(
                        f"{tag} format 15 glyph IDs do not fit in format 14"
                    )
                key = _cmap_subtable_key(subtable)
                format14 = format14_by_key.get(key)
                if format14 is None:
                    format14 = _copy_uvs_subtable(14, subtable)
                    format14_by_key[key] = format14
                    tables.append(format14)
                else:
                    format14.ensureDecompiled()
                    _merge_uvs_dict(format14.uvsDict, subtable.uvsDict)
                continue
            tables.append(subtable)
        character_map.tables = tables


def _drop_beyond64k_cmap_format4(font: TTFont) -> None:
    if (
        not any(tag in font for tag in ("cmap", "DMAP"))
        or len(font.getGlyphOrder()) <= 0x10000
    ):
        return

    for _, character_map in _character_map_tables(font):
        unicode_bmp_tables = [
            subtable
            for subtable in character_map.tables
            if subtable.format == 4 and subtable.isUnicode() and not subtable.isSymbol()
        ]
        if not unicode_bmp_tables:
            continue
        if not any(subtable.format == 12 for subtable in character_map.tables):
            cmap12 = {}
            for subtable in unicode_bmp_tables:
                cmap12.update(subtable.cmap)
            if cmap12:
                from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

                subtable = CmapSubtable.newSubtable(12)
                subtable.platformID = 3
                subtable.platEncID = 10
                subtable.language = 0
                subtable.cmap = cmap12
                character_map.tables.append(subtable)

        character_map.tables = [
            subtable
            for subtable in character_map.tables
            if subtable not in unicode_bmp_tables
        ]


def _drop_beyond64k_post_glyph_names(font: TTFont) -> None:
    # post 2.0 numberOfGlyphs is uint16: drop above 0xFFFF, not 0x10000.
    if "post" not in font or len(font.getGlyphOrder()) <= 0xFFFF:
        return

    post = font["post"]
    if post.formatType == 2.0:
        post.formatType = 3.0
        post.extraNames = []
        post.mapping = {}


def _convert_table(
    font: TTFont,
    source,
    source_tag: str,
    conversion: _TableConversion,
    overwrite: bool,
) -> None:
    destination_tag = conversion.destination
    if conversion.transform is not None:
        conversion.transform(font, source, overwrite)
    if source_tag == destination_tag:
        return
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
    table_conversions: dict[str, _TableConversion],
    validate: bool,
    overwrite: bool,
    ignore_missing: bool,
    validate_conversion=None,
) -> None:
    tables = _normalize_tables(tables)
    conversions = {
        source: conversion
        for source, conversion in table_conversions.items()
        if _TABLE_IDENTITIES[source] in tables
    }
    if validate_conversion is not None:
        validate_conversion(font, conversions)

    pending = []
    for source_tag, conversion in conversions.items():
        destination_tag = conversion.destination
        source_exists = source_tag in font
        destination_exists = destination_tag in font

        if (
            source_tag != destination_tag
            and source_exists
            and destination_exists
            and not overwrite
        ):
            raise ValueError(
                f"Both {source_tag!r} and {destination_tag!r} exist; "
                "set overwrite=True to replace the destination"
            )
        if not source_exists:
            if destination_exists or ignore_missing:
                continue
            raise KeyError(source_tag)
        pending.append((source_tag, conversion))

    if validate:
        result_tags = set(font.keys())
        for source_tag, conversion in pending:
            destination_tag = conversion.destination
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
    for source_tag, conversion in pending:
        _convert_table(font, sources[source_tag], source_tag, conversion, overwrite)

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
    """Convert selected tables to their beyond-64k companion forms.

    Args:
        font: Font to modify in place.
        tables: Optional iterable of table tags to convert. If omitted, all
            supported tables present in ``font`` are converted. Tags may use
            either spelling of a companion table family, such as ``"glyf"`` or
            ``"GLYF"``.
        validate: If true, reject conversions that leave the font with a mixed
            lowercase/uppercase companion table family.
        overwrite: If true, replace an existing destination table. Otherwise an
            existing destination raises ``ValueError``.
        ignore_missing: If true, requested source tables that are not present
            are ignored unless their destination is already present. Otherwise
            missing source tables raise ``KeyError``.
    """
    _convert_tables(
        font,
        tables=tables,
        table_conversions=_UPPER_TABLES,
        validate=validate,
        overwrite=overwrite,
        ignore_missing=ignore_missing,
    )
    _upper_beyond64k_cmap_uvs(font)
    _drop_beyond64k_cmap_format4(font)
    _drop_beyond64k_post_glyph_names(font)


def lower_tables(
    font: TTFont,
    *,
    tables: Iterable[str] | None = None,
    validate: bool = True,
    overwrite: bool = False,
    ignore_missing: bool = True,
) -> None:
    """Convert selected tables from their beyond-64k companion forms.

    Args are the same as :func:`upper_tables`. In addition to mixed-family
    validation, lowering rejects data that cannot be represented in compact
    tables, including glyph counts above 65535, cubic ``GLYF`` outlines, and
    component glyph IDs that do not fit in ``glyf``.
    """
    _convert_tables(
        font,
        tables=tables,
        table_conversions=_LOWER_TABLES,
        validate=validate,
        overwrite=overwrite,
        ignore_missing=ignore_missing,
        validate_conversion=_validate_lowering,
    )
    _lower_beyond64k_cmap_uvs(font)


def main(args=None):
    parser = argparse.ArgumentParser(
        "fonttools ttLib.beyond64k",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "direction",
        choices=("upper", "lower"),
        help="'upper' converts to beyond-64k companions; 'lower' converts back",
    )
    parser.add_argument("input", metavar="INPUT", help="input font path")
    parser.add_argument(
        "tables",
        metavar="TABLE",
        nargs="*",
        help="optional table tags to convert, e.g. GSUB GPOS glyf",
    )
    parser.add_argument("-o", "--output", metavar="OUTPUT", help="output font path")
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="skip mixed-family and lossy-lowering validation",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace destination tables if they already exist",
    )
    parser.add_argument(
        "--no-ignore-missing",
        dest="ignore_missing",
        action="store_false",
        help="raise an error when a requested source table is missing",
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
