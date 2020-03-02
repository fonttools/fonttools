from fontTools.misc.py23 import *
from fontTools.varLib.models import (
    normalizeLocation, supportScalar, VariationModel, VariationModelError)
import pytest


def test_normalizeLocation():
    axes = {"wght": (100, 400, 900)}
    assert normalizeLocation({"wght": 400}, axes) == {'wght': 0.0}
    assert normalizeLocation({"wght": 100}, axes) == {'wght': -1.0}
    assert normalizeLocation({"wght": 900}, axes) == {'wght': 1.0}
    assert normalizeLocation({"wght": 650}, axes) == {'wght': 0.5}
    assert normalizeLocation({"wght": 1000}, axes) == {'wght': 1.0}
    assert normalizeLocation({"wght": 0}, axes) == {'wght': -1.0}

    axes = {"wght": (0, 0, 1000)}
    assert normalizeLocation({"wght": 0}, axes) == {'wght': 0.0}
    assert normalizeLocation({"wght": -1}, axes) == {'wght': 0.0}
    assert normalizeLocation({"wght": 1000}, axes) == {'wght': 1.0}
    assert normalizeLocation({"wght": 500}, axes) == {'wght': 0.5}
    assert normalizeLocation({"wght": 1001}, axes) == {'wght': 1.0}

    axes = {"wght": (0, 1000, 1000)}
    assert normalizeLocation({"wght": 0}, axes) == {'wght': -1.0}
    assert normalizeLocation({"wght": -1}, axes) == {'wght': -1.0}
    assert normalizeLocation({"wght": 500}, axes) == {'wght': -0.5}
    assert normalizeLocation({"wght": 1000}, axes) == {'wght': 0.0}
    assert normalizeLocation({"wght": 1001}, axes) == {'wght': 0.0}


def test_supportScalar():
    assert supportScalar({}, {}) == 1.0
    assert supportScalar({'wght':.2}, {}) == 1.0
    assert supportScalar({'wght':.2}, {'wght':(0,2,3)}) == 0.1
    assert supportScalar({'wght':2.5}, {'wght':(0,2,4)}) == 0.75


class VariationModelTest(object):

    @pytest.mark.parametrize(
        "locations, axisOrder, sortedLocs, supports, deltaWeights",
        [
            (
                [
                    {'wght': 0.55, 'wdth': 0.0},
                    {'wght': -0.55, 'wdth': 0.0},
                    {'wght': -1.0, 'wdth': 0.0},
                    {'wght': 0.0, 'wdth': 1.0},
                    {'wght': 0.66, 'wdth': 1.0},
                    {'wght': 0.66, 'wdth': 0.66},
                    {'wght': 0.0, 'wdth': 0.0},
                    {'wght': 1.0, 'wdth': 1.0},
                    {'wght': 1.0, 'wdth': 0.0},
                ],
                ["wght"],
                [
                    {},
                    {'wght': -0.55},
                    {'wght': -1.0},
                    {'wght': 0.55},
                    {'wght': 1.0},
                    {'wdth': 1.0},
                    {'wdth': 1.0, 'wght': 1.0},
                    {'wdth': 1.0, 'wght': 0.66},
                    {'wdth': 0.66, 'wght': 0.66}
                ],
                [
                    {},
                    {'wght': (-1.0, -0.55, 0)},
                    {'wght': (-1.0, -1.0, -0.55)},
                    {'wght': (0, 0.55, 1.0)},
                    {'wght': (0.55, 1.0, 1.0)},
                    {'wdth': (0, 1.0, 1.0)},
                    {'wdth': (0, 1.0, 1.0), 'wght': (0, 1.0, 1.0)},
                    {'wdth': (0, 1.0, 1.0), 'wght': (0, 0.66, 1.0)},
                    {'wdth': (0, 0.66, 1.0), 'wght': (0, 0.66, 1.0)}
                ],
                [
                    {},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0,
                     4: 1.0,
                     5: 1.0},
                    {0: 1.0,
                     3: 0.7555555555555555,
                     4: 0.24444444444444444,
                     5: 1.0,
                     6: 0.66},
                    {0: 1.0,
                     3: 0.7555555555555555,
                     4: 0.24444444444444444,
                     5: 0.66,
                     6: 0.43560000000000006,
                     7: 0.66}
                ]
            ),
            (
                [
                    {},
                    {'bar': 0.5},
                    {'bar': 1.0},
                    {'foo': 1.0},
                    {'bar': 0.5, 'foo': 1.0},
                    {'bar': 1.0, 'foo': 1.0},
                ],
                None,
                [
                    {},
                    {'bar': 0.5},
                    {'bar': 1.0},
                    {'foo': 1.0},
                    {'bar': 0.5, 'foo': 1.0},
                    {'bar': 1.0, 'foo': 1.0},
                ],
                [
                    {},
                    {'bar': (0, 0.5, 1.0)},
                    {'bar': (0.5, 1.0, 1.0)},
                    {'foo': (0, 1.0, 1.0)},
                    {'bar': (0, 0.5, 1.0), 'foo': (0, 1.0, 1.0)},
                    {'bar': (0.5, 1.0, 1.0), 'foo': (0, 1.0, 1.0)},
                ],
                [
                    {},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0, 1: 1.0, 3: 1.0},
                    {0: 1.0, 2: 1.0, 3: 1.0},
                ],
            )
        ]
    )
    def test_init(
        self, locations, axisOrder, sortedLocs, supports, deltaWeights
    ):
        model = VariationModel(locations, axisOrder=axisOrder)

        assert model.locations == sortedLocs
        assert model.supports == supports
        assert model.deltaWeights == deltaWeights

    def test_init_duplicate_locations(self):
        with pytest.raises(VariationModelError, match="Locations must be unique."):
            VariationModel(
                [
                    {"foo": 0.0, "bar": 0.0},
                    {"foo": 1.0, "bar": 1.0},
                    {"bar": 1.0, "foo": 1.0},
                ]
            )
