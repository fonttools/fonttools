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
                    {'bar': 0.25},
                    {'bar': 0.75},
                    {'bar': 1.0},
                ],
                None,
                False,
                [
                    {},
                    {'bar': 0.25},
                    {'bar': 0.75},
                    {'bar': 1.0},
                    {'foo': 0.25},
                    {'foo': 0.5},
                    {'foo': 0.75},
                    {'foo': 1.0},
                ],
                [
                    {},
                    {'bar': (0, 0.25, 1.0)},
                    {'bar': (0.25, 0.75, 1.0)},
                    {'bar': (0.75, 1.0, 1.0)},
                    {'foo': (0, 0.25, 1.0)},
                    {'foo': (0.25, 0.5, 1.0)},
                    {'foo': (0.5, 0.75, 1.0)},
                    {'foo': (0.75, 1.0, 1.0)},
                ],
                [
                    {},
                    {0: 1.0},
                    {0: 1.0, 1: 0.3333333333333333},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0, 4: 0.6666666666666666},
                    {0: 1.0, 4: 0.3333333333333333, 5: 0.5},
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
                    {'bar': 0.25},
                    {'bar': 0.75},
                    {'bar': 1.0},
                ],
                None,
                True,
                [
                    {},
                    {'bar': 0.25},
                    {'bar': 0.75},
                    {'bar': 1.0},
                    {'foo': 0.25},
                    {'foo': 0.5},
                    {'foo': 0.75},
                    {'foo': 1.0},
                ],
                [
                    {},
                    {'bar': (0, 0.25, 0.75)},
                    {'bar': (0.25, 0.75, 1.0)},
                    {'bar': (0.75, 1.0, 1.0)},
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

    def test_equivalency_of_simple_regions(self):
        from random import seed, randint, random
        axisPoints = dict(
            a=[0, 0.3, 0.8, 1],
            b=[-1, -0.7, -0.2, 0],
            c=[-1, 0, 1],
            d=[0],
            e=[0],
        )
        locations = [[]]
        for axis, points in axisPoints.items():
            locations = [loc + [(axis, v)] for loc in locations for v in points]
        locations = [dict(loc) for loc in locations]
        # Add a disconnected sub-system
        locations.extend([dict(d=1), dict(e=1), dict(d=1, e=1)])
        genericModel = VariationModel(locations)
        simpleModel = VariationModel(locations, preferSimpleRegions=True)
        assert genericModel.locations == simpleModel.locations
        assert genericModel.supports != simpleModel.supports
        assert genericModel.deltaWeights != simpleModel.deltaWeights
        seed(0)
        testLocations = locations + [
            dict(a=random(), b=random() - 1, c=2 * random() - 1, d=random(), e=random())
            for _ in range(100)
        ]
        masterValues = [randint(0, 100) for _ in range(len(locations))]
        deltas1 = genericModel.getDeltas(masterValues)
        deltas2 = simpleModel.getDeltas(masterValues)
        import time
        t = time.time()
        for loc in testLocations:
            value1 = genericModel.interpolateFromDeltas(loc, deltas1)
            value2 = simpleModel.interpolateFromDeltas(loc, deltas2)
            assert math.isclose(value1, value2, abs_tol=1e-09)
