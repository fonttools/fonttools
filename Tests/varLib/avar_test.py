from fontTools.varLib.avar import _pruneLocations
import unittest
import pytest


@pytest.mark.parametrize(
    "locations, poles, expected",
    [
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
    ],
)
def test_pruneLocations(locations, poles, expected):
    axisTags = set()
    for location in locations:
        axisTags.update(location.keys())
    axisTags = sorted(axisTags)

    locations = [{}] + locations

    output = _pruneLocations(locations, poles, axisTags)

    assert output == expected, (output, expected)
