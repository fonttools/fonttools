#!/usr/bin/env python3
"""Script to remove redundant font name table records."""
from fontTools.ttLib.ttVisitor import TTVisitor
from fontTools import ttLib
from fontTools.ttLib import TTFont
import fontTools.ttLib.tables.otTables as otTables
from fontTools.ttLib.tables import C_P_A_L_
import sys
import logging


logger = logging.getLogger()


class NameRecordVisitor(TTVisitor):
    def __init__(self):
        self.seen = set()

    def removeUnusedNameRecords(self, font):
        self.visit(font)
        toDelete = set()
        for record in font["name"].names:
            # Name IDs 26 to 255, inclusive, are reserved for future standard names.
            # https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids
            if record.nameID < 256:
                continue
            if record.nameID not in self.seen:
                toDelete.add(record.nameID)

        if not toDelete:
            logger.info("Name table has no redundant records, skipping")
            return
        logger.info(f"Deleting name records with NameIDs {toDelete}")
        for nameID in toDelete:
            font["name"].removeNames(nameID)


@NameRecordVisitor.register_attrs(
    (
        (otTables.FeatureParamsSize, ("SubfamilyID", "SubfamilyNameID")),
        (otTables.FeatureParamsStylisticSet, ("UINameID",)),
        (
            otTables.FeatureParamsCharacterVariants,
            (
                "FeatUILabelNameID",
                "FeatUITooltipTextNameID",
                "SampleTextNameID",
                "FirstParamUILabelNameID",
            ),
        ),
        (otTables.STAT, ("ElidedFallbackNameID",)),
        (otTables.AxisRecord, ("AxisNameID",)),
        (otTables.AxisValue, ("ValueNameID",)),
        (otTables.FeatureName, ("FeatureNameID",)),
        (otTables.Setting, ("SettingNameID",)),
    )
)
def visit(visitor, obj, attr, value):
    visitor.seen.add(value)


@NameRecordVisitor.register(ttLib.getTableClass("fvar"))
def visit(visitor, obj):
    for inst in obj.instances:
        visitor.seen.add(inst.postscriptNameID)
        visitor.seen.add(inst.subfamilyNameID)

    for axis in obj.axes:
        visitor.seen.add(axis.axisNameID)


@NameRecordVisitor.register(ttLib.getTableClass("CPAL"))
def visit(visitor, obj):
    for nameID in obj.paletteLabels:
        if nameID != C_P_A_L_.table_C_P_A_L_.NO_NAME_ID:
            visitor.seen.add(nameID)


def removeUnusedNameRecords(ttFont):
    visitor = NameRecordVisitor()
    visitor.removeUnusedNameRecords(ttFont)


def main():
    if len(sys.argv) != 3:
        print("Usage: python nameClean.py font.ttf out.ttf")
        sys.exit()
    font = TTFont(sys.argv[1])
    removeUnusedNameRecords(font)
    font.save(sys.argv[2])


if __name__ == "__main__":
    main()
