"""Helpers for instantiating name table records."""

from contextlib import contextmanager
from copy import deepcopy
from enum import IntEnum
import re


class NameID(IntEnum):
    FAMILY_NAME = 1
    SUBFAMILY_NAME = 2
    UNIQUE_FONT_IDENTIFIER = 3
    FULL_FONT_NAME = 4
    VERSION_STRING = 5
    POSTSCRIPT_NAME = 6
    TYPOGRAPHIC_FAMILY_NAME = 16
    TYPOGRAPHIC_SUBFAMILY_NAME = 17
    VARIATIONS_POSTSCRIPT_NAME_PREFIX = 25


ELIDABLE_AXIS_VALUE_NAME = 2


def getVariationNameIDs(varfont):
    used = []
    if "fvar" in varfont:
        fvar = varfont["fvar"]
        for axis in fvar.axes:
            used.append(axis.axisNameID)
        for instance in fvar.instances:
            used.append(instance.subfamilyNameID)
            if instance.postscriptNameID != 0xFFFF:
                used.append(instance.postscriptNameID)
    if "STAT" in varfont:
        stat = varfont["STAT"].table
        for axis in stat.DesignAxisRecord.Axis if stat.DesignAxisRecord else ():
            used.append(axis.AxisNameID)
        for value in stat.AxisValueArray.AxisValue if stat.AxisValueArray else ():
            used.append(value.ValueNameID)
    # nameIDs <= 255 are reserved by OT spec so we don't touch them
    return {nameID for nameID in used if nameID > 255}


@contextmanager
def pruningUnusedNames(varfont):
    from . import log

    origNameIDs = getVariationNameIDs(varfont)

    yield

    log.info("Pruning name table")
    exclude = origNameIDs - getVariationNameIDs(varfont)
    varfont["name"].names[:] = [
        record for record in varfont["name"].names if record.nameID not in exclude
    ]
    if "ltag" in varfont:
        # Drop the whole 'ltag' table if all the language-dependent Unicode name
        # records that reference it have been dropped.
        # TODO: Only prune unused ltag tags, renumerating langIDs accordingly.
        # Note ltag can also be used by feat or morx tables, so check those too.
        if not any(
            record
            for record in varfont["name"].names
            if record.platformID == 0 and record.langID != 0xFFFF
        ):
            del varfont["ltag"]


def updateNameTable(varfont, axisLimits):
    """Update an instatiated variable font's name table using the Axis
    Values from the STAT table.

    The updated name table will conform to the R/I/B/BI naming model.
    """
    # This task can be split into two parts:

    # Task 1: Collecting and sorting the relevant AxisValues:
    # 1. First check the variable font has a STAT table and it contains
    #    AxisValues.
    # 2. Create a dictionary which contains the pinned axes from the
    #    axisLimits dict and for the unpinned axes, we'll use the fvar
    #    default coordinates e.g
    #    axisLimits = {"wght": 500, "wdth": AxisRange(75, 100), our dict will
    #    be {"wght": 500, "wdth": 100} if the width axis has a default of 100.
    # 3. Create a new list of AxisValues whose Values match the dict we just
    #    created.
    # 4. Remove any AxisValues from the list which have the
    #    Elidable_AXIS_VALUE_NAME flag set.
    # 5. Remove and sort AxisValues in the list so format 4 AxisValues take
    #    precedence. According to the MS Spec "if a format 1, format 2 or
    #    format 3 table has a (nominal) value used in a format 4 table that
    #    also has values for other axes, the format 4 table, being the more
    #    specific match, is used",
    #    https://docs.microsoft.com/en-us/typography/opentype/spec/stat#axis-value-table-format-4

    # Task 2: Updating a name table's style and family names from a list of
    # AxisValues:
    # 1. Sort AxisValues into two groups. For the first group, the names must be
    #    any of the following ["Regular", "Italic", "Bold", "Bold Italic"].
    #    This group of names is often referred to as "RIBBI" names. For the
    #    other group, names must be non-RIBBI e.g "Medium Italic", "Condensed"
    #    etc.
    # 2. Repeat the next steps for each name table record platform:
    #    a. Create new subFamily name and Typographic subFamily name from the
    #       above groups.
    #    b. Update nameIDs 1, 2, 3, 4, 6, 16, 17 using the new name created
    #       in the last step.
    #
    # Step by step example:
    # A variable font which has a width and weight axes.
    # AxisValues in font (represented as simplified dicts):
    # axisValues = [
    #     {"name": "Light", "axis": "wght", "value": 300},
    #     {"name": "Regular", "axis": "wght", "value": 400},
    #     {"name": "Medium", "axis": "wght", "value": 500},
    #     {"name": "Bold", "axis": "wght", "value": 600},
    #     {"name": "Condensed", "axis": "wdth", "value": 75},
    #     {"name": "Normal", "axis": "wdth", "value": 100, "flags": 0x2},
    # ]
    # # Let's instantiate a partial font which has a pinned wght axis and an
    #   unpinned width axis.
    # >>> axisLimits = {"wght": 500, "width": AxisRange(75, 100)}
    # >>> updateNameTable(varfont, axisLimits)
    #
    # AxisValues remaining after task 1.3:
    # axisValues = [
    #     {"name": "Medium", "axis": "wght", "value": 500},
    #     {"name": "Normal", "axis": "wdth", "value": 100, "flags": 0x2}
    # ]
    #
    # AxisValues remaining after completing all 1.x tasks:
    # axisValues = [{"name": "Medium", "axis": "wght", "value": 500}]
    # The Normal AxisValue is removed because it has the
    # Elidable_AXIS_VALUE_NAME flag set.
    #
    # # AxisValues after separating into two groups in task 2.1:
    # ribbiAxisValues = []
    # nonRibbiAxisValues = [{"name": "Medium", "axis": "wght", "value": 500}]
    #
    # # Names created from AxisValues in task 2.2a for Win US English platform:
    # subFamilyName = ""
    # typoSubFamilyName = "Medium"
    #
    # NameRecords updated in task 2.2b for Win US English platform:
    # NameID 1 familyName: "Open Sans" --> "Open Sans Medium"
    # NameID 2 subFamilyName: "Regular" --> "Regular"
    # NameID 3 Unique font identifier: "3.000;GOOG;OpenSans-Regular" --> \
    #     "3.000;GOOG;OpenSans-Medium"
    # NameID 4 Full font name: "Open Sans Regular" --> "Open Sans Medium"
    # NameID 6 PostScript name: "OpenSans-Regular" --> "OpenSans-Medium"
    # NameID 16 Typographic Family name: None --> "Open Sans"
    # NameID 17 Typographic Subfamily name: None --> "Medium"
    #
    # Notes on name table record updates:
    # - Typographic names have been added since Medium is a non-Ribbi name.
    # - Neither the before or after name records include the Width AxisValue
    #   names because the "Normal" AxisValue has the
    #   Elidable_AXIS_VALUE_NAME flag set.
    #   If we instantiate the same font but pin the wdth axis to 75,
    #   the "Condensed" AxisValue will be included.
    # - For info regarding how RIBBI and non-RIBBI can be constructed see:
    # https://docs.microsoft.com/en-us/typography/opentype/spec/name#name-ids
    from . import AxisRange, axisValuesFromAxisLimits

    if "STAT" not in varfont:
        raise ValueError("Cannot update name table since there is no STAT table.")
    stat = varfont["STAT"].table
    if not stat.AxisValueArray:
        raise ValueError("Cannot update name table since there are no STAT Axis Values")
    fvar = varfont["fvar"]

    # The updated name table must reflect the new 'zero origin' of the font.
    # If we're instantiating a partial font, we will populate the unpinned
    # axes with their default axis values.
    fvarDefaults = {a.axisTag: a.defaultValue for a in fvar.axes}
    defaultAxisCoords = deepcopy(axisLimits)
    for axisTag, val in fvarDefaults.items():
        if axisTag not in defaultAxisCoords or isinstance(
            defaultAxisCoords[axisTag], AxisRange
        ):
            defaultAxisCoords[axisTag] = val

    axisValueTables = axisValuesFromAxisLimits(stat, defaultAxisCoords)
    checkAxisValuesExist(stat, axisValueTables, defaultAxisCoords)

    # Remove axis Values which have ELIDABLE_AXIS_VALUE_NAME flag set.
    # Axis Values which have this flag enabled won't be visible in
    # application font menus.
    axisValueTables = [
        v for v in axisValueTables if not v.Flags & ELIDABLE_AXIS_VALUE_NAME
    ]
    axisValueTables = _sortAxisValues(axisValueTables)
    _updateNameRecords(varfont, axisValueTables)


def checkAxisValuesExist(stat, axisValues, axisCoords):
    seen = set()
    designAxes = stat.DesignAxisRecord.Axis
    for axisValueTable in axisValues:
        axisValueFormat = axisValueTable.Format
        if axisValueTable.Format in (1, 2, 3):
            axisTag = designAxes[axisValueTable.AxisIndex].AxisTag
            if axisValueFormat == 2:
                axisValue = axisValueTable.NominalValue
            else:
                axisValue = axisValueTable.Value
            if axisTag in axisCoords and axisValue == axisCoords[axisTag]:
                seen.add(axisTag)
        elif axisValueTable.Format == 4:
            for rec in axisValueTable.AxisValueRecord:
                axisTag = designAxes[rec.AxisIndex].AxisTag
                if axisTag in axisCoords and rec.Value == axisCoords[axisTag]:
                    seen.add(axisTag)

    missingAxes = set(axisCoords) - seen
    if missingAxes:
        missing = ", ".join(f"'{i}={axisCoords[i]}'" for i in missingAxes)
        raise ValueError(f"Cannot find Axis Values [{missing}]")


def _sortAxisValues(axisValues):
    # Sort and remove duplicates ensuring that format 4 Axis Values
    # are dominant
    results = []
    seenAxes = set()
    # Sort format 4 axes so the tables with the most AxisValueRecords
    # are first
    format4 = sorted(
        [v for v in axisValues if v.Format == 4],
        key=lambda v: len(v.AxisValueRecord),
        reverse=True,
    )
    nonFormat4 = [v for v in axisValues if v not in format4]

    for val in format4:
        axisIndexes = set(r.AxisIndex for r in val.AxisValueRecord)
        minIndex = min(axisIndexes)
        if not seenAxes & axisIndexes:
            seenAxes |= axisIndexes
            results.append((minIndex, val))

    for val in nonFormat4:
        axisIndex = val.AxisIndex
        if axisIndex not in seenAxes:
            seenAxes.add(axisIndex)
            results.append((axisIndex, val))

    return [axisValue for _, axisValue in sorted(results)]


def _updateNameRecords(varfont, axisValues):
    # Update nametable based on the axisValues using the R/I/B/BI model.
    nametable = varfont["name"]
    stat = varfont["STAT"].table

    axisValueNameIDs = [a.ValueNameID for a in axisValues]
    ribbiNameIDs = [n for n in axisValueNameIDs if nameIDIsRibbi(nametable, n)]
    nonRibbiNameIDs = [n for n in axisValueNameIDs if n not in ribbiNameIDs]
    elidedNameID = stat.ElidedFallbackNameID
    elidedNameIsRibbi = nameIDIsRibbi(nametable, elidedNameID)

    getName = nametable.getName
    platforms = set((r.platformID, r.platEncID, r.langID) for r in nametable.names)
    for platform in platforms:
        if not all(getName(i, *platform) for i in (1, 2, elidedNameID)):
            # Since no family name and subfamily name records were found,
            # we cannot update this set of name Records.
            continue

        subFamilyName = " ".join(
            getName(n, *platform).toUnicode() for n in ribbiNameIDs
        )
        typoSubFamilyName = " ".join(
            getName(n, *platform).toUnicode()
            for n in axisValueNameIDs
            if nonRibbiNameIDs
        )

        # If neither subFamilyName and typographic SubFamilyName exist,
        # we will use the STAT's elidedFallbackName
        if not typoSubFamilyName and not subFamilyName:
            if elidedNameIsRibbi:
                subFamilyName = getName(elidedNameID, *platform).toUnicode()
            else:
                typoSubFamilyName = getName(elidedNameID, *platform).toUnicode()

        familyNameSuffix = " ".join(
            getName(n, *platform).toUnicode() for n in nonRibbiNameIDs
        )

        _updateNameTableStyleRecords(
            varfont,
            familyNameSuffix,
            subFamilyName,
            typoSubFamilyName,
            *platform,
        )


def nameIDIsRibbi(nametable, nameID):
    engNameRecords = any(
        r
        for r in nametable.names
        if (r.platformID, r.platEncID, r.langID) == (3, 1, 0x409)
    )
    if not engNameRecords:
        raise ValueError(
            f"Canot determine if there are RIBBI Axis Value Tables "
            "since there are no name table Records which have "
            "platformID=3, platEncID=1, langID=0x409"
        )
    return (
        True
        if nametable.getName(nameID, 3, 1, 0x409).toUnicode()
        in ("Regular", "Italic", "Bold", "Bold Italic")
        else False
    )


def _updateNameTableStyleRecords(
    varfont,
    familyNameSuffix,
    subFamilyName,
    typoSubFamilyName,
    platformID=3,
    platEncID=1,
    langID=0x409,
):
    # TODO (Marc F) It may be nice to make this part a standalone
    # font renamer in the future.
    nametable = varfont["name"]
    platform = (platformID, platEncID, langID)

    currentFamilyName = nametable.getName(
        NameID.TYPOGRAPHIC_FAMILY_NAME, *platform
    ) or nametable.getName(NameID.FAMILY_NAME, *platform)

    currentStyleName = nametable.getName(
        NameID.TYPOGRAPHIC_SUBFAMILY_NAME, *platform
    ) or nametable.getName(NameID.SUBFAMILY_NAME, *platform)

    currentFamilyName = currentFamilyName.toUnicode()
    currentStyleName = currentStyleName.toUnicode()

    nameIDs = {
        NameID.FAMILY_NAME: currentFamilyName,
        NameID.SUBFAMILY_NAME: subFamilyName,
    }
    if typoSubFamilyName:
        nameIDs[NameID.FAMILY_NAME] = f"{currentFamilyName} {familyNameSuffix}".strip()
        nameIDs[NameID.TYPOGRAPHIC_FAMILY_NAME] = currentFamilyName
        nameIDs[NameID.TYPOGRAPHIC_SUBFAMILY_NAME] = f"{typoSubFamilyName}"
    # Remove previous Typographic Family and SubFamily names since they're
    # no longer required
    else:
        for nameID in (
            NameID.TYPOGRAPHIC_FAMILY_NAME,
            NameID.TYPOGRAPHIC_SUBFAMILY_NAME,
        ):
            nametable.removeNames(nameID=nameID)

    newFamilyName = (
        nameIDs.get(NameID.TYPOGRAPHIC_FAMILY_NAME) or nameIDs[NameID.FAMILY_NAME]
    )
    newStyleName = (
        nameIDs.get(NameID.TYPOGRAPHIC_SUBFAMILY_NAME) or nameIDs[NameID.SUBFAMILY_NAME]
    )

    nameIDs[NameID.FULL_FONT_NAME] = f"{newFamilyName} {newStyleName}"
    nameIDs[NameID.POSTSCRIPT_NAME] = _updatePSNameRecord(
        varfont, newFamilyName, newStyleName, platform
    )
    nameIDs[NameID.UNIQUE_FONT_IDENTIFIER] = _updateUniqueIdNameRecord(
        varfont, nameIDs, platform
    )

    for nameID, string in nameIDs.items():
        if not string:
            continue
        nametable.setName(string, nameID, *platform)


def _updatePSNameRecord(varfont, familyName, styleName, platform):
    # Implementation based on Adobe Technical Note #5902 :
    # https://wwwimages2.adobe.com/content/dam/acom/en/devnet/font/pdfs/5902.AdobePSNameGeneration.pdf
    nametable = varfont["name"]

    family_prefix = nametable.getName(
        NameID.VARIATIONS_POSTSCRIPT_NAME_PREFIX, *platform
    )
    if family_prefix:
        family_prefix = family_prefix.toUnicode()
    else:
        family_prefix = familyName

    psName = f"{family_prefix}-{styleName}"
    # Remove any characters other than uppercase Latin letters, lowercase
    # Latin letters, digits and hyphens.
    psName = re.sub(r"[^A-Za-z0-9-]", r"", psName)

    if len(psName) > 127:
        # Abbreviating the stylename so it fits within 127 characters whilst
        # conforming to every vendor's specification is too complex. Instead
        # we simply truncate the psname and add the required "..."
        return f"{psName[:124]}..."
    return psName


def _updateUniqueIdNameRecord(varfont, nameIDs, platform):
    nametable = varfont["name"]
    currentRecord = nametable.getName(NameID.UNIQUE_FONT_IDENTIFIER, *platform)
    if not currentRecord:
        return None

    # Check if full name and postscript name are a substring of currentRecord
    for nameID in (NameID.FULL_FONT_NAME, NameID.POSTSCRIPT_NAME):
        nameRecord = nametable.getName(nameID, *platform)
        if not nameRecord:
            continue
        if currentRecord.toUnicode() in nameRecord.toUnicode():
            return currentRecord.toUnicode().replace(
                nameRecord.toUnicode(), nameIDs[nameRecord.nameID]
            )
    # Create a new string since we couldn't find any substrings.
    fontVersion = _fontVersion(varfont, platform)
    achVendID = varfont["OS/2"].achVendID
    # Remove non-ASCII characers and trailing spaces
    vendor = re.sub(r"[^\x00-\x7F]", "", achVendID).strip()
    psName = nameIDs[NameID.POSTSCRIPT_NAME]
    return f"{fontVersion};{vendor};{psName}"


def _fontVersion(font, platform=(3, 1, 0x409)):
    nameRecord = font["name"].getName(NameID.VERSION_STRING, *platform)
    if nameRecord is None:
        return f'{font["head"].fontRevision:.3f}'
    # "Version 1.101; ttfautohint (v1.8.1.43-b0c9)" --> "1.101"
    # Also works fine with inputs "Version 1.101" or "1.101" etc
    versionNumber = nameRecord.toUnicode().split(";")[0]
    return versionNumber.lstrip("Version ").strip()
