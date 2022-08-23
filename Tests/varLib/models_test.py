from fontTools.varLib.models import (
    normalizeLocation,
    supportScalar,
    VariationModel,
    VariationModelError,
)
import pytest


def test_normalizeLocation():
    axes = {"wght": (100, 400, 900)}
    assert normalizeLocation({"wght": 400}, axes) == {"wght": 0.0}
    assert normalizeLocation({"wght": 100}, axes) == {"wght": -1.0}
    assert normalizeLocation({"wght": 900}, axes) == {"wght": 1.0}
    assert normalizeLocation({"wght": 650}, axes) == {"wght": 0.5}
    assert normalizeLocation({"wght": 1000}, axes) == {"wght": 1.0}
    assert normalizeLocation({"wght": 0}, axes) == {"wght": -1.0}

    axes = {"wght": (0, 0, 1000)}
    assert normalizeLocation({"wght": 0}, axes) == {"wght": 0.0}
    assert normalizeLocation({"wght": -1}, axes) == {"wght": 0.0}
    assert normalizeLocation({"wght": 1000}, axes) == {"wght": 1.0}
    assert normalizeLocation({"wght": 500}, axes) == {"wght": 0.5}
    assert normalizeLocation({"wght": 1001}, axes) == {"wght": 1.0}

    axes = {"wght": (0, 1000, 1000)}
    assert normalizeLocation({"wght": 0}, axes) == {"wght": -1.0}
    assert normalizeLocation({"wght": -1}, axes) == {"wght": -1.0}
    assert normalizeLocation({"wght": 500}, axes) == {"wght": -0.5}
    assert normalizeLocation({"wght": 1000}, axes) == {"wght": 0.0}
    assert normalizeLocation({"wght": 1001}, axes) == {"wght": 0.0}


def test_supportScalar():
    assert supportScalar({}, {}) == 1.0
    assert supportScalar({"wght": 0.2}, {}) == 1.0
    assert supportScalar({"wght": 0.2}, {"wght": (0, 2, 3)}) == 0.1
    assert supportScalar({"wght": 2.5}, {"wght": (0, 2, 4)}) == 0.75
    assert supportScalar({"wght": 4}, {"wght": (0, 2, 2)}) == 0.0
    assert supportScalar({"wght": 4}, {"wght": (0, 2, 2)}, extrapolate=True) == 2.0
    assert supportScalar({"wght": 4}, {"wght": (0, 2, 3)}, extrapolate=True) == 2.0
    assert supportScalar({"wght": 2}, {"wght": (0, .75, 1)}, extrapolate=True) == -4.0


@pytest.mark.parametrize(
    "numLocations, numSamples",
    [
        pytest.param(127, 509, marks=pytest.mark.slow),
        (31, 251),
    ],
)
def test_modeling_error(numLocations, numSamples):
    # https://github.com/fonttools/fonttools/issues/2213
    locations = [{"axis": float(i) / numLocations} for i in range(numLocations)]
    masterValues = [100.0 if i else 0.0 for i in range(numLocations)]

    model = VariationModel(locations)

    for i in range(numSamples):
        loc = {"axis": float(i) / numSamples}
        scalars = model.getScalars(loc)

        deltas_float = model.getDeltas(masterValues)
        deltas_round = model.getDeltas(masterValues, round=round)

        expected = model.interpolateFromDeltasAndScalars(deltas_float, scalars)
        actual = model.interpolateFromDeltasAndScalars(deltas_round, scalars)

        err = abs(actual - expected)
        assert err <= 0.5, (i, err)

        # This is how NOT to round deltas.
        # deltas_late_round = [round(d) for d in deltas_float]
        # bad = model.interpolateFromDeltasAndScalars(deltas_late_round, scalars)
        # err_bad = abs(bad - expected)
        # if err != err_bad:
        #    print("{:d}	{:.2}	{:.2}".format(i, err, err_bad))


class VariationModelTest(object):
    @pytest.mark.parametrize(
        "locations, axisOrder, sortedLocs, supports, deltaWeights",
        [
            (
                [
                    {"wght": 0.55, "wdth": 0.0},
                    {"wght": -0.55, "wdth": 0.0},
                    {"wght": -1.0, "wdth": 0.0},
                    {"wght": 0.0, "wdth": 1.0},
                    {"wght": 0.66, "wdth": 1.0},
                    {"wght": 0.66, "wdth": 0.66},
                    {"wght": 0.0, "wdth": 0.0},
                    {"wght": 1.0, "wdth": 1.0},
                    {"wght": 1.0, "wdth": 0.0},
                ],
                ["wght"],
                [
                    {},
                    {"wght": -0.55},
                    {"wght": -1.0},
                    {"wght": 0.55},
                    {"wght": 1.0},
                    {"wdth": 1.0},
                    {"wdth": 1.0, "wght": 1.0},
                    {"wdth": 1.0, "wght": 0.66},
                    {"wdth": 0.66, "wght": 0.66},
                ],
                [
                    {},
                    {"wght": (-1.0, -0.55, 0)},
                    {"wght": (-1.0, -1.0, -0.55)},
                    {"wght": (0, 0.55, 1.0)},
                    {"wght": (0.55, 1.0, 1.0)},
                    {"wdth": (0, 1.0, 1.0)},
                    {"wdth": (0, 1.0, 1.0), "wght": (0.66, 1.0, 1.0)},
                    {"wdth": (0.66, 1.0, 1.0), "wght": (0, 0.66, 1.0)},
                    {"wdth": (0, 0.66, 1.0), "wght": (0, 0.66, 1.0)},
                ],
                [
                    {},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0},
                    {0: 1.0, 4: 1.0, 5: 1.0},
                    {0: 1.0, 3: 0.7555555555555555, 4: 0.24444444444444444, 5: 1.0},
                    {0: 1.0, 3: 0.7555555555555555, 4: 0.24444444444444444, 5: 0.66},
                ],
            ),
            (
                [
                    {},
                    {"bar": 0.5},
                    {"bar": 1.0},
                    {"foo": 1.0},
                    {"bar": 0.5, "foo": 1.0},
                    {"bar": 1.0, "foo": 1.0},
                ],
                None,
                [
                    {},
                    {"bar": 0.5},
                    {"bar": 1.0},
                    {"foo": 1.0},
                    {"bar": 0.5, "foo": 1.0},
                    {"bar": 1.0, "foo": 1.0},
                ],
                [
                    {},
                    {"bar": (0, 0.5, 1.0)},
                    {"bar": (0.5, 1.0, 1.0)},
                    {"foo": (0, 1.0, 1.0)},
                    {"bar": (0, 0.5, 1.0), "foo": (0, 1.0, 1.0)},
                    {"bar": (0.5, 1.0, 1.0), "foo": (0, 1.0, 1.0)},
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
                    {"foo": 0.25},
                    {"foo": 0.5},
                    {"foo": 0.75},
                    {"foo": 1.0},
                    {"bar": 0.25},
                    {"bar": 0.75},
                    {"bar": 1.0},
                ],
                None,
                [
                    {},
                    {"bar": 0.25},
                    {"bar": 0.75},
                    {"bar": 1.0},
                    {"foo": 0.25},
                    {"foo": 0.5},
                    {"foo": 0.75},
                    {"foo": 1.0},
                ],
                [
                    {},
                    {"bar": (0.0, 0.25, 0.75)},
                    {"bar": (0.25, 0.75, 1.0)},
                    {"bar": (0.75, 1.0, 1.0)},
                    {"foo": (0.0, 0.25, 0.5)},
                    {"foo": (0.25, 0.5, 0.75)},
                    {"foo": (0.5, 0.75, 1.0)},
                    {"foo": (0.75, 1.0, 1.0)},
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
            (
                [
                    {},
                    {"foo": 0.25},
                    {"foo": 0.5},
                    {"foo": 0.75},
                    {"foo": 1.0},
                    {"bar": 0.25},
                    {"bar": 0.75},
                    {"bar": 1.0},
                ],
                None,
                [
                    {},
                    {"bar": 0.25},
                    {"bar": 0.75},
                    {"bar": 1.0},
                    {"foo": 0.25},
                    {"foo": 0.5},
                    {"foo": 0.75},
                    {"foo": 1.0},
                ],
                [
                    {},
                    {"bar": (0, 0.25, 0.75)},
                    {"bar": (0.25, 0.75, 1.0)},
                    {"bar": (0.75, 1.0, 1.0)},
                    {"foo": (0, 0.25, 0.5)},
                    {"foo": (0.25, 0.5, 0.75)},
                    {"foo": (0.5, 0.75, 1.0)},
                    {"foo": (0.75, 1.0, 1.0)},
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
        ],
    )
    def test_init(self, locations, axisOrder, sortedLocs, supports, deltaWeights):
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
