# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod, Roozbeh Pournader

from collections import OrderedDict
from fontTools import ttLib, cffLib
from fontTools.merge.base import add_method, mergeObjects
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables._n_a_m_e import NameRecordVisitor, NameDict
from fontTools.merge.util import *
import logging


log = logging.getLogger("fontTools.merge")


def restoreFontSpecificNames(name, names, ttFont=None):
    if isinstance(names, list):
        nameIDs = [
            name.addMultilingualName(
                n, ttFont, windows=getattr(n, "hasWindows"), mac=getattr(n, "hasMac")
            )
            for n in names
        ]
        return nameIDs

    return name.addMultilingualName(
        names,
        ttFont,
        windows=getattr(names, "hasWindows"),
        mac=getattr(names, "hasMac"),
    )


def concat(lst, sep="; ", distinct=True):
    return sep.join(set(lst) if distinct else lst)


def distinctCharacters(lst):
    return "".join(OrderedDict.fromkeys("".join(lst)))


def mergeNames(lst, merge):
    # concat all names on per-language basis
    # if an item does not have given language, use first available

    if len(lst) == 1:
        return lst[0]

    languages = set()
    names = NameDict()

    for n in lst:
        languages.update(n)
        names.platforms.update(n.platforms)

    for lang in languages:
        langNames = [n.get(lang, next(iter(n.values()))) for n in lst if n]
        names[lang] = merge(langNames)

    return names


def setNames(obj, attr, lst, merge):
    merged = mergeNames([getattr(l, attr + "Names") for l in lst], merge)
    setattr(obj, attr + "Names", merged)


def namesPreMerge(font):
    name = font.get("name")
    if name:
        visitor = NameRecordStoringVisitor()
        visitor.visit(font)


def namesPostMerge(font):
    name = font.get("name")
    if name:
        visitor = NameRecordRestoringVisitor()
        visitor.visit(font)


@add_method(ttLib.getTableClass("name"))
def merge(self, m, tables):
    DefaultTable.merge(self, m, tables)
    if m.options.merge_names:
        allNameIDs = set.union(*[table.getNameIDs(maxNameID=255) for table in tables])

        mergedNames = dict()
        for nameID in allNameIDs:
            lst = [table.getNames(nameID) for table in tables]
            mergedNames[nameID] = mergeNames(lst, concat)

        self.names = []
        for nameID in sorted(mergedNames):
            mergedName = mergedNames[nameID]
            self.addMultilingualName(
                mergedName,
                m.mega,
                nameID,
                mergedName.hasWindows(),
                mergedName.hasMac(),
            )

    return self


class NameRecordStoringVisitor(NameRecordVisitor):
    def see(self, obj, attr, value):
        log.debug(" %s %s", attr, str(value))
        if attr == "FirstParamUILabelNameID":
            value = range(value, value + obj.NumNamedParameters)

        name = self.font.get("name")
        if name:
            names = (
                name.getNames(value)
                if isinstance(value, int)
                else [name.getNames(v) for v in value]
            )
            setattr(obj, attr + "Names", names)


class NameRecordRestoringVisitor(NameRecordVisitor):
    def see(self, obj, attr, value):
        names = getattr(obj, attr)

        if names:
            name = self.font.get("name")
            if name:
                nameID = restoreFontSpecificNames(name, names, self.font)
                setattr(obj, attr[: -len("Names")], nameID)
                log.debug("  %s %s", attr[: -len("Names")], str(nameID))

            delattr(obj, attr)


@NameRecordRestoringVisitor.register_attrs(
    (
        (otTables.FeatureParamsSize, ("SubfamilyIDNames", "SubfamilyNameIDNames")),
        (otTables.FeatureParamsStylisticSet, ("UINameIDNames",)),
        (
            otTables.FeatureParamsCharacterVariants,
            (
                "FeatUILabelNameIDNames",
                "FeatUITooltipTextNameIDNames",
                "SampleTextNameIDNames",
                "FirstParamUILabelNameIDNames",
            ),
        ),
        (otTables.STAT, ("ElidedFallbackNameIDNames",)),
        (otTables.AxisRecord, ("AxisNameIDNames",)),
        (otTables.AxisValue, ("ValueNameIDNames",)),
        (otTables.FeatureName, ("FeatureNameIDNames",)),
        (otTables.Setting, ("SettingNameIDNames",)),
    )
)
def visit(visitor, obj, attr, value):
    visitor.see(obj, attr, value)
