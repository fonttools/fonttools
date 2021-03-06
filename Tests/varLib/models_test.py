import math
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
        "locations, axisOrder, simple, sortedLocs, supports, deltaWeights",
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
                False,
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
                False,
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
            ),
            (
                [
                    {},
                    {'foo': 0.25},
                    {'foo': 0.5},
                    {'foo': 0.75},
                    {'foo': 1.0},
                ],
                None,
                False,
                [
                    {},
                    {'foo': 0.25},
                    {'foo': 0.5},
                    {'foo': 0.75},
                    {'foo': 1.0},
                ],
                [
                    {},
                    {'foo': (0, 0.25, 1.0)},
                    {'foo': (0.25, 0.5, 1.0)},
                    {'foo': (0.5, 0.75, 1.0)},
                    {'foo': (0.75, 1.0, 1.0)},
                ],
                [
                    {},
                    {0: 1.0},
                    {0: 1.0, 1: 0.6666666666666666},
                    {0: 1.0, 1: 0.3333333333333333, 2: 0.5},
                    {0: 1.0},
                ],
            ),
            (
                [
                    {},
                    {'foo': 0.25},
                    {'foo': 0.5},
                    {'foo': 0.75},
                    {'foo': 1.0},
                ],
                None,
                True,
                [
                    {},
                    {'foo': 0.25},
                    {'foo': 0.5},
                    {'foo': 0.75},
                    {'foo': 1.0},
                ],
                [
                    {},
                    {'foo': (0, 0.25, 0.5)},
                    {'foo': (0.25, 0.5, 0.75)},
                    {'foo': (0.5, 0.75, 1.0)},
                    {'foo': (0.75, 1.0, 1.0)},
                ],
                [
                    {},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                ],
            ),
        ]
    )
    def test_init(
        self, locations, axisOrder, simple, sortedLocs, supports, deltaWeights
    ):
        model = VariationModel(
            locations, axisOrder=axisOrder, preferSimpleRegions=simple
        )

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

    @staticmethod
    def _make_test_locations(axisPoints, steps):
        locations = [[]]
        for axis, points in axisPoints.items():
            minValue = min(points)
            extent = max(points) - minValue
            values = [
                (axis, minValue + extent * i / (steps - 1))
                for i in range(steps)
            ]
            locations = [loc + [v] for loc in locations for v in values]
        return [dict(loc) for loc in locations]

    def test_equivalency_of_simple_regions(self):
        from random import seed, randint
        axisPoints = dict(
            a=[0, 0.25, 0.75, 1],
            b=[-1, -0.75, -0.25, 0],
            c=[-1, 0, 1],
        )
        locations = [[]]
        for axis, points in axisPoints.items():
            locations = [loc + [(axis, v)] for loc in locations for v in points]
        locations = [dict(loc) for loc in locations]
        genericModel = VariationModel(locations)
        simpleModel = VariationModel(locations, preferSimpleRegions=True)
        assert genericModel.locations == simpleModel.locations
        assert genericModel.supports != simpleModel.supports
        assert genericModel.deltaWeights != simpleModel.deltaWeights
        testLocations = self._make_test_locations(axisPoints, 5)
        seed(0)
        masterValues = [randint(0, 100) for _ in range(len(locations))]
        deltas1 = genericModel.getDeltas(masterValues)
        deltas2 = simpleModel.getDeltas(masterValues)
        for loc in testLocations:
            value1 = genericModel.interpolateFromDeltas(loc, deltas1)
            value2 = simpleModel.interpolateFromDeltas(loc, deltas2)
            assert math.isclose(value1, value2)
