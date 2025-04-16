from collections import OrderedDict
from fontTools.designspaceLib import AxisDescriptor
from fontTools.ttLib import TTFont, newTable
from fontTools import varLib
from fontTools.varLib.featureVars import (
    addFeatureVariations,
    overlayFeatureVariations,
    overlayBox,
)
import pytest


def makeVariableFont(glyphOrder, axes):
    font = TTFont()
    font.setGlyphOrder(glyphOrder)
    font["name"] = newTable("name")
    ds_axes = OrderedDict()
    for axisTag, (minimum, default, maximum) in axes.items():
        axis = AxisDescriptor()
        axis.name = axis.tag = axis.labelNames["en"] = axisTag
        axis.minimum, axis.default, axis.maximum = minimum, default, maximum
        ds_axes[axisTag] = axis
    varLib._add_fvar(font, ds_axes, instances=())
    return font


@pytest.fixture
def varfont():
    return makeVariableFont(
        [".notdef", "space", "A", "B", "A.alt", "B.alt"],
        {"wght": (100, 400, 900)},
    )


def test_addFeatureVariations(varfont):
    assert "GSUB" not in varfont

    addFeatureVariations(varfont, [([{"wght": (0.5, 1.0)}], {"A": "A.alt"})])

    assert "GSUB" in varfont
    gsub = varfont["GSUB"].table

    assert len(gsub.ScriptList.ScriptRecord) == 1
    assert gsub.ScriptList.ScriptRecord[0].ScriptTag == "DFLT"

    assert len(gsub.FeatureList.FeatureRecord) == 1
    assert gsub.FeatureList.FeatureRecord[0].FeatureTag == "rvrn"

    assert len(gsub.LookupList.Lookup) == 1
    assert gsub.LookupList.Lookup[0].LookupType == 1
    assert len(gsub.LookupList.Lookup[0].SubTable) == 1
    assert gsub.LookupList.Lookup[0].SubTable[0].mapping == {"A": "A.alt"}

    assert gsub.FeatureVariations is not None
    assert len(gsub.FeatureVariations.FeatureVariationRecord) == 1
    fvr = gsub.FeatureVariations.FeatureVariationRecord[0]
    assert len(fvr.ConditionSet.ConditionTable) == 1
    cst = fvr.ConditionSet.ConditionTable[0]
    assert cst.AxisIndex == 0
    assert cst.FilterRangeMinValue == 0.5
    assert cst.FilterRangeMaxValue == 1.0
    assert len(fvr.FeatureTableSubstitution.SubstitutionRecord) == 1
    ftsr = fvr.FeatureTableSubstitution.SubstitutionRecord[0]
    assert ftsr.FeatureIndex == 0
    assert ftsr.Feature.LookupListIndex == [0]


def _substitution_features(gsub, rec_index):
    fea_tags = [feature.FeatureTag for feature in gsub.FeatureList.FeatureRecord]
    fea_indices = [
        gsub.FeatureVariations.FeatureVariationRecord[rec_index]
        .FeatureTableSubstitution.SubstitutionRecord[i]
        .FeatureIndex
        for i in range(
            len(
                gsub.FeatureVariations.FeatureVariationRecord[
                    rec_index
                ].FeatureTableSubstitution.SubstitutionRecord
            )
        )
    ]
    return [(i, fea_tags[i]) for i in fea_indices]


def test_addFeatureVariations_existing_variable_feature(varfont):
    assert "GSUB" not in varfont

    addFeatureVariations(varfont, [([{"wght": (0.5, 1.0)}], {"A": "A.alt"})])

    gsub = varfont["GSUB"].table
    assert len(gsub.FeatureList.FeatureRecord) == 1
    assert gsub.FeatureList.FeatureRecord[0].FeatureTag == "rvrn"
    assert len(gsub.FeatureVariations.FeatureVariationRecord) == 1
    assert _substitution_features(gsub, rec_index=0) == [(0, "rvrn")]

    # can't add feature variations for an existing feature tag that already has some,
    # in this case the default 'rvrn'
    with pytest.raises(
        varLib.VarLibError,
        match=r"FeatureVariations already exist for feature tag\(s\): {'rvrn'}",
    ):
        addFeatureVariations(varfont, [([{"wght": (0.5, 1.0)}], {"A": "A.alt"})])


def test_addFeatureVariations_new_feature(varfont):
    assert "GSUB" not in varfont

    addFeatureVariations(varfont, [([{"wght": (0.5, 1.0)}], {"A": "A.alt"})])

    gsub = varfont["GSUB"].table
    assert len(gsub.FeatureList.FeatureRecord) == 1
    assert gsub.FeatureList.FeatureRecord[0].FeatureTag == "rvrn"
    assert len(gsub.LookupList.Lookup) == 1
    assert len(gsub.FeatureVariations.FeatureVariationRecord) == 1
    assert _substitution_features(gsub, rec_index=0) == [(0, "rvrn")]

    # we can add feature variations for a feature tag that does not have
    # any feature variations yet
    addFeatureVariations(
        varfont, [([{"wght": (-1.0, 0.0)}], {"B": "B.alt"})], featureTag="rclt"
    )

    assert len(gsub.FeatureList.FeatureRecord) == 2
    # Note 'rclt' is now first (index=0) in the feature list sorted by tag, and
    # 'rvrn' is second (index=1)
    assert gsub.FeatureList.FeatureRecord[0].FeatureTag == "rclt"
    assert gsub.FeatureList.FeatureRecord[1].FeatureTag == "rvrn"
    assert len(gsub.LookupList.Lookup) == 2
    assert len(gsub.FeatureVariations.FeatureVariationRecord) == 2
    # The new 'rclt' feature variation record is appended to the end;
    # the feature index for 'rvrn' feature table substitution record is now 1
    assert _substitution_features(gsub, rec_index=0) == [(1, "rvrn")]
    assert _substitution_features(gsub, rec_index=1) == [(0, "rclt")]


def test_addFeatureVariations_existing_condition(varfont):
    assert "GSUB" not in varfont

    # Add a feature variation for 'ccmp' feature tag with a condition
    addFeatureVariations(
        varfont, [([{"wght": (0.5, 1.0)}], {"A": "A.alt"})], featureTag="ccmp"
    )

    gsub = varfont["GSUB"].table

    # Should now have one feature record, one lookup, and one feature variation record
    assert len(gsub.FeatureList.FeatureRecord) == 1
    assert gsub.FeatureList.FeatureRecord[0].FeatureTag == "ccmp"
    assert len(gsub.LookupList.Lookup) == 1
    assert len(gsub.FeatureVariations.FeatureVariationRecord) == 1
    assert _substitution_features(gsub, rec_index=0) == [(0, "ccmp")]

    # Add a feature variation for 'rlig' feature tag with the same condition
    addFeatureVariations(
        varfont, [([{"wght": (0.5, 1.0)}], {"B": "B.alt"})], featureTag="rlig"
    )

    # Should now have two feature records, two lookups, and one feature variation
    # record, since the condition is the same for both feature variations
    assert len(gsub.FeatureList.FeatureRecord) == 2
    assert gsub.FeatureList.FeatureRecord[0].FeatureTag == "ccmp"
    assert gsub.FeatureList.FeatureRecord[1].FeatureTag == "rlig"
    assert len(gsub.LookupList.Lookup) == 2
    assert len(gsub.FeatureVariations.FeatureVariationRecord) == 1
    assert _substitution_features(gsub, rec_index=0) == [(0, "ccmp"), (1, "rlig")]


def _test_linear(n):
    conds = []
    for i in range(n):
        end = i / n
        start = end - 1.0
        region = [{"X": (start, end)}]
        subst = {"g%.2g" % start: "g%.2g" % end}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    assert len(overlaps) == 2 * n - 1, overlaps
    return conds, overlaps


def test_linear():
    _test_linear(10)


def _test_quadratic(n):
    conds = []
    for i in range(1, n + 1):
        region = [{"X": (0, i / n), "Y": (0, (n + 1 - i) / n)}]
        subst = {str(i): str(n + 1 - i)}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    assert len(overlaps) == n * (n + 1) // 2, overlaps
    return conds, overlaps


def test_quadratic():
    _test_quadratic(10)


def _merge_substitutions(substitutions):
    merged = {}
    for subst in substitutions:
        merged.update(subst)
    return merged


def _match_condition(location, overlaps):
    for box, substitutions in overlaps:
        for tag, coord in location.items():
            start, end = box[tag]
            if start <= coord <= end:
                return _merge_substitutions(substitutions)
    return {}  # no match


def test_overlaps_1():
    # https://github.com/fonttools/fonttools/issues/1400
    conds = [
        ([{"abcd": (4, 9)}], {0: 0}),
        ([{"abcd": (5, 10)}], {1: 1}),
        ([{"abcd": (0, 8)}], {2: 2}),
        ([{"abcd": (3, 7)}], {3: 3}),
    ]
    overlaps = overlayFeatureVariations(conds)
    subst = _match_condition({"abcd": 0}, overlaps)
    assert subst == {2: 2}
    subst = _match_condition({"abcd": 1}, overlaps)
    assert subst == {2: 2}
    subst = _match_condition({"abcd": 3}, overlaps)
    assert subst == {2: 2, 3: 3}
    subst = _match_condition({"abcd": 4}, overlaps)
    assert subst == {0: 0, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 5}, overlaps)
    assert subst == {0: 0, 1: 1, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 7}, overlaps)
    assert subst == {0: 0, 1: 1, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 8}, overlaps)
    assert subst == {0: 0, 1: 1, 2: 2}
    subst = _match_condition({"abcd": 9}, overlaps)
    assert subst == {0: 0, 1: 1}
    subst = _match_condition({"abcd": 10}, overlaps)
    assert subst == {1: 1}


def test_overlaps_2():
    # https://github.com/fonttools/fonttools/issues/1400
    conds = [
        ([{"abcd": (1, 9)}], {0: 0}),
        ([{"abcd": (8, 10)}], {1: 1}),
        ([{"abcd": (3, 4)}], {2: 2}),
        ([{"abcd": (1, 10)}], {3: 3}),
    ]
    overlaps = overlayFeatureVariations(conds)
    subst = _match_condition({"abcd": 0}, overlaps)
    assert subst == {}
    subst = _match_condition({"abcd": 1}, overlaps)
    assert subst == {0: 0, 3: 3}
    subst = _match_condition({"abcd": 2}, overlaps)
    assert subst == {0: 0, 3: 3}
    subst = _match_condition({"abcd": 3}, overlaps)
    assert subst == {0: 0, 2: 2, 3: 3}
    subst = _match_condition({"abcd": 5}, overlaps)
    assert subst == {0: 0, 3: 3}
    subst = _match_condition({"abcd": 10}, overlaps)
    assert subst == {1: 1, 3: 3}


def test_overlayBox():
    # https://github.com/fonttools/fonttools/issues/3003
    top = {"opsz": (0.75, 1.0), "wght": (0.5, 1.0)}
    bot = {"wght": (0.25, 1.0)}
    intersection, remainder = overlayBox(top, bot)
    assert intersection == {"opsz": (0.75, 1.0), "wght": (0.5, 1.0)}
    assert remainder == {"wght": (0.25, 1.0)}


def run(test, n, quiet):
    print()
    print("%s:" % test.__name__)
    input, output = test(n)
    if quiet:
        print(len(output))
    else:
        print()
        print("Input:")
        pprint(input)
        print()
        print("Output:")
        pprint(output)
        print()


if __name__ == "__main__":
    import sys
    from pprint import pprint

    quiet = False
    n = 3
    if len(sys.argv) > 1 and sys.argv[1] == "-q":
        quiet = True
        del sys.argv[1]
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    run(_test_linear, n=n, quiet=quiet)
    run(_test_quadratic, n=n, quiet=quiet)
