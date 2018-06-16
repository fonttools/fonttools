from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.varLib.models import (
    normalizeLocation, supportScalar, VariationModel)


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


def test_VariationModel():
    locations = [
        {'wght':100},
        {'wght':-100},
        {'wght':-180},
        {'wdth':+.3},
        {'wght':+120,'wdth':.3},
        {'wght':+120,'wdth':.2},
        {},
        {'wght':+180,'wdth':.3},
        {'wght':+180},
    ]
    model = VariationModel(locations, axisOrder=['wght'])

    assert model.locations == [
        {},
        {'wght': -100},
        {'wght': -180},
        {'wght': 100},
        {'wght': 180},
        {'wdth': 0.3},
        {'wdth': 0.3, 'wght': 180},
        {'wdth': 0.3, 'wght': 120},
        {'wdth': 0.2, 'wght': 120}]

    assert model.deltaWeights == [
        {},
        {0: 1.0},
        {0: 1.0},
        {0: 1.0},
        {0: 1.0},
        {0: 1.0},
        {0: 1.0, 4: 1.0, 5: 1.0},
        {0: 1.0, 3: 0.75, 4: 0.25, 5: 1.0, 6: 0.6666666666666666},
        {0: 1.0,
         3: 0.75,
         4: 0.25,
         5: 0.6666666666666667,
         6: 0.4444444444444445,
         7: 0.6666666666666667}]

def test_VariationModel():
    locations = [
        {},
        {'bar': 0.5},
        {'bar': 1.0},
        {'foo': 1.0},
        {'bar': 0.5, 'foo': 1.0},
        {'bar': 1.0, 'foo': 1.0},
    ]
    model = VariationModel(locations)

    assert model.locations == locations

    assert model.supports == [
        {},
        {'bar': (0, 0.5, 1.0)},
        {'bar': (0.5, 1.0, 1.0)},
        {'foo': (0, 1.0, 1.0)},
        {'bar': (0, 0.5, 1.0), 'foo': (0, 1.0, 1.0)},
        {'bar': (0.5, 1.0, 1.0), 'foo': (0, 1.0, 1.0)},
    ]
