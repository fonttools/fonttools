from fontTools.ttLib import TTFont
from fontTools.varLib.models import VariationModel
from fontTools.varLib.avar import _pruneLocations, mappings_from_avar
import os
import unittest
import pytest

TESTS = [
    (
        [
            {"wght": 1},
            {"wght": 0.5},
        ],
        [
            {"wght": 0.5},
        ],
        [
            {"wght": 0.5},
        ],
    ),
    (
        [
            {"wght": 1, "wdth": 1},
            {"wght": 0.5, "wdth": 1},
        ],
        [
            {"wght": 1, "wdth": 1},
        ],
        [
            {"wght": 1, "wdth": 1},
            {"wght": 0.5, "wdth": 1},
        ],
    ),
    (
        [
            {"wght": 1},
            {"wdth": 1},
            {"wght": 0.5, "wdth": 0.5},
        ],
        [
            {"wght": 0.5, "wdth": 0.5},
        ],
        [
            {"wght": 0.5, "wdth": 0.5},
        ],
    ),
]


@pytest.mark.parametrize("locations, poles, expected", TESTS)
def test_pruneLocations(locations, poles, expected):
    axisTags = set()
    for location in locations:
        axisTags.update(location.keys())
    axisTags = sorted(axisTags)

    locations = [{}] + locations

    pruned = _pruneLocations(locations, poles, axisTags)

    assert pruned == expected, (pruned, expected)


@pytest.mark.parametrize("locations, poles, expected", TESTS)
def test_roundtrip(locations, poles, expected):
    axisTags = set()
    for location in locations:
        axisTags.update(location.keys())
    axisTags = sorted(axisTags)

    locations = [{}] + locations
    expected = [{}] + expected

    model1 = VariationModel(locations, axisTags)
    model2 = VariationModel(expected, axisTags)

    for location in poles:
        i = model1.locations.index(location)
        support1 = model1.supports[i]

        i = model2.locations.index(location)
        support2 = model2.supports[i]

        assert support1 == support2, (support1, support2)


def test_mappings_from_avar():
    CWD = os.path.abspath(os.path.dirname(__file__))
    DATADIR = os.path.join(CWD, "..", "ttLib", "tables", "data")
    varfont_path = os.path.join(DATADIR, "Amstelvar-avar2.subset.ttf")
    font = TTFont(varfont_path)
    mappings = mappings_from_avar(font)

    assert len(mappings) == 2, mappings
