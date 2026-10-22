from io import BytesIO

import pytest

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.psCharStrings import T2CharString
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.varLib.builder import buildVarData
from fontTools.varLib.models import supportScalar


def reload(font):
    buf = BytesIO()
    font.save(buf)
    buf.seek(0)
    return TTFont(buf)


def makeFont():
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "PrivateDict", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    fb.setupFvar([("wght", 0, 0, 1, "Weight"), ("wdth", 0, 0, 1, "Width")], [])
    fb.setupCFF2(
        {".notdef": T2CharString(program=[])},
        fdArrayList=[
            {
                # The builder also accepts blends on these non-blendable fields.
                "BlueScale": [0.039625, 0.02, 0.01],
                "ExpansionFactor": [0.06, 0.03, 0.02],
                "StdHW": [80.25, 0.02, 0.01],
                "StdVW": [90.5, 0.03, 0.02],
                "StemSnapH": [[80.25, 0.02, 0.01], [100.5, 0.03, 0.02]],
                "StemSnapV": [[90.5, 0.03, 0.02], [120.75, 0.04, 0.03]],
                "BlueValues": [[-20, 3, 5], [0, 0, 0]],
            }
        ],
        regions=[{"wght": (0, 1, 1)}, {"wdth": (0, 1, 1)}],
    )
    return reload(fb.font)


def privateValues(font, name, location):
    topDict = font["CFF2"].cff.topDictIndex[0]
    private = topDict.FDArray[0].Private
    values = getattr(private, name)
    if name not in {"StemSnapH", "StemSnapV", "BlueValues"}:
        values = [values]
    scalars = []
    if hasattr(topDict, "VarStore"):
        axes = font["fvar"].axes
        store = topDict.VarStore.otVarStore
        data = store.VarData[getattr(private, "vsindex", 0)]
        scalars = [
            supportScalar(location, store.VarRegionList.Region[i].get_support(axes))
            for i in data.VarRegionIndex
        ]
    result = []
    adjustment = 0
    for value in values:
        if isinstance(value, list):
            delta = sum(d * scalar for d, scalar in zip(value[1:], scalars))
            if name in {"StemSnapH", "StemSnapV", "BlueValues"}:
                adjustment += delta
            else:
                adjustment = delta
            value = value[0] + adjustment
        result.append(value)
    return result


REAL_FIELDS = [
    "BlueScale",
    "ExpansionFactor",
    "StdHW",
    "StdVW",
    "StemSnapH",
    "StemSnapV",
]


@pytest.mark.parametrize("name", REAL_FIELDS)
@pytest.mark.parametrize(
    "limits, samples",
    [
        (
            {},
            [
                (location, location)
                for location in ({}, {"wght": 0.5, "wdth": 0.5}, {"wght": 1, "wdth": 1})
            ],
        ),
        ({"wght": 0.5, "wdth": 0.5}, [({}, {"wght": 0.5, "wdth": 0.5})]),
        (
            {"wght": 0.5},
            [({"wdth": width}, {"wght": 0.5, "wdth": width}) for width in (0, 0.5, 1)],
        ),
        (
            {"wght": (0, 0.5, 1)},
            [
                ({"wght": weight}, {"wght": (weight + 1) / 2})
                for weight in (-1, -0.5, 0, 0.5, 1)
            ],
        ),
        (
            {"wght": (0, 0.5, 1), "wdth": 0.5},
            [
                ({"wght": weight}, {"wght": (weight + 1) / 2, "wdth": 0.5})
                for weight in (-1, -0.5, 0, 0.5, 1)
            ],
        ),
    ],
)
def test_fractional_private_blends(name, limits, samples):
    original = makeFont()
    instance = reload(instancer.instantiateVariableFont(original, limits))

    for location, originalLocation in samples:
        assert privateValues(instance, name, location) == pytest.approx(
            privateValues(original, name, originalLocation), rel=0, abs=1e-10
        )


def test_integer_private_blends_still_round():
    font = makeFont()
    instancer.instantiateCFF2(
        font, instancer.NormalizedAxisLimits({"wght": (0, 0.5, 1), "wdth": 0})
    )
    font = reload(font)

    assert privateValues(font, "BlueValues", {}) == [-18, 2]
    assert privateValues(font, "BlueValues", {"wght": 1}) == [-16, 4]


@pytest.mark.parametrize("name", REAL_FIELDS)
def test_fractional_private_blends_inherited_vsindex(name):
    original = makeFont()
    topDict = original["CFF2"].cff.topDictIndex[0]
    private = topDict.FDArray[0].Private
    store = topDict.VarStore.otVarStore
    store.VarData.insert(0, buildVarData([], []))
    store.VarDataCount += 1
    private.vsindex = 1
    original = reload(original)

    instance = reload(
        instancer.instantiateVariableFont(original, {"wght": (0, 0.5, 1), "wdth": 0.5})
    )

    assert privateValues(instance, name, {}) == pytest.approx(
        privateValues(original, name, {"wght": 0.5, "wdth": 0.5}), rel=0, abs=1e-10
    )


@pytest.mark.parametrize("name", REAL_FIELDS)
def test_fractional_private_blends_repeated_instancing(name):
    original = makeFont()
    partial = reload(instancer.instantiateVariableFont(original, {"wght": (0, 0.5, 1)}))
    instance = reload(
        instancer.instantiateVariableFont(partial, {"wght": 0.75, "wdth": 0.5})
    )

    assert privateValues(instance, name, {}) == pytest.approx(
        privateValues(original, name, {"wght": 0.75, "wdth": 0.5}), rel=0, abs=1e-10
    )


@pytest.mark.parametrize("name", REAL_FIELDS)
def test_fractional_private_blends_culling(name):
    original = makeFont()
    instance = reload(original)
    instancer.instantiateCFF2(
        instance,
        instancer.NormalizedAxisLimits({}),
        reachableRanges={"wdth": (-1, -0.5)},
    )
    instance = reload(instance)

    for weight in (0, 0.5, 1):
        location = {"wght": weight}
        assert privateValues(instance, name, location) == pytest.approx(
            privateValues(original, name, location), rel=0, abs=1e-10
        )
