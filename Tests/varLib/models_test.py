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


@pytest.mark.parametrize(
    "axes, location, expected",
    [
        # lower != default != upper
        ({"wght": (100, 400, 900)}, {"wght": 1000}, {"wght": 1.2}),
        ({"wght": (100, 400, 900)}, {"wght": 900}, {"wght": 1.0}),
        ({"wght": (100, 400, 900)}, {"wght": 650}, {"wght": 0.5}),
        ({"wght": (100, 400, 900)}, {"wght": 400}, {"wght": 0.0}),
        ({"wght": (100, 400, 900)}, {"wght": 250}, {"wght": -0.5}),
        ({"wght": (100, 400, 900)}, {"wght": 100}, {"wght": -1.0}),
        ({"wght": (100, 400, 900)}, {"wght": 25}, {"wght": -1.25}),
        # lower == default != upper
        (
            {"wght": (400, 400, 900), "wdth": (100, 100, 150)},
            {"wght": 1000, "wdth": 200},
            {"wght": 1.2, "wdth": 2.0},
        ),
        (
            {"wght": (400, 400, 900), "wdth": (100, 100, 150)},
            {"wght": 25, "wdth": 25},
            {"wght": -0.75, "wdth": -1.5},
        ),
        # lower != default == upper
        (
            {"wght": (100, 400, 400), "wdth": (50, 100, 100)},
            {"wght": 700, "wdth": 150},
            {"wght": 1.0, "wdth": 1.0},
        ),
        (
            {"wght": (100, 400, 400), "wdth": (50, 100, 100)},
            {"wght": -50, "wdth": 25},
            {"wght": -1.5, "wdth": -1.5},
        ),
        # degenerate case with lower == default == upper, normalized location always 0
        ({"wght": (400, 400, 400)}, {"wght": 100}, {"wght": 0.0}),
        ({"wght": (400, 400, 400)}, {"wght": 400}, {"wght": 0.0}),
        ({"wght": (400, 400, 400)}, {"wght": 700}, {"wght": 0.0}),
    ],
)
def test_normalizeLocation_extrapolate(axes, location, expected):
    assert normalizeLocation(location, axes, extrapolate=True) == expected


def test_supportScalar():
    assert supportScalar({}, {}) == 1.0
    assert supportScalar({"wght": 0.2}, {}) == 1.0
    assert supportScalar({"wght": 0.2}, {"wght": (0, 2, 3)}) == 0.1
    assert supportScalar({"wght": 2.5}, {"wght": (0, 2, 4)}) == 0.75
    assert supportScalar({"wght": 3}, {"wght": (0, 2, 2)}) == 0.0
    assert (
        supportScalar(
            {"wght": 3},
            {"wght": (0, 2, 2)},
            extrapolate=True,
            axisRanges={"wght": (0, 2)},
        )
        == 1.5
    )
    assert (
        supportScalar(
            {"wght": -1},
            {"wght": (0, 2, 2)},
            extrapolate=True,
            axisRanges={"wght": (0, 2)},
        )
        == -0.5
    )
    assert (
        supportScalar(
            {"wght": 3},
            {"wght": (0, 1, 2)},
            extrapolate=True,
            axisRanges={"wght": (0, 2)},
        )
        == -1.0
    )
    assert (
        supportScalar(
            {"wght": -1},
            {"wght": (0, 1, 2)},
            extrapolate=True,
            axisRanges={"wght": (0, 2)},
        )
        == -1.0
    )
    assert (
        supportScalar(
            {"wght": 2},
            {"wght": (0, 0.75, 1)},
            extrapolate=True,
            axisRanges={"wght": (0, 1)},
        )
        == -4.0
    )
    with pytest.raises(TypeError):
        supportScalar(
            {"wght": 2}, {"wght": (0, 0.75, 1)}, extrapolate=True, axisRanges=None
        )


def test_model_extrapolate():
    locations = [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}]
    model = VariationModel(locations, extrapolate=True)
    masterValues = [100, 200, 300, 400]
    testLocsAndValues = [
        ({"a": -1, "b": -1}, -200),
        ({"a": -1, "b": 0}, 0),
        ({"a": -1, "b": 1}, 200),
        ({"a": -1, "b": 2}, 400),
        ({"a": 0, "b": -1}, -100),
        ({"a": 0, "b": 0}, 100),
        ({"a": 0, "b": 1}, 300),
        ({"a": 0, "b": 2}, 500),
        ({"a": 1, "b": -1}, 0),
        ({"a": 1, "b": 0}, 200),
        ({"a": 1, "b": 1}, 400),
        ({"a": 1, "b": 2}, 600),
        ({"a": 2, "b": -1}, 100),
        ({"a": 2, "b": 0}, 300),
        ({"a": 2, "b": 1}, 500),
        ({"a": 2, "b": 2}, 700),
    ]
    for loc, expectedValue in testLocsAndValues:
        assert expectedValue == model.interpolateFromMasters(loc, masterValues)


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
                    {"wdth": (0, 1.0, 1.0), "wght": (0, 1.0, 1.0)},
                    {"wdth": (0, 1.0, 1.0), "wght": (0, 0.66, 1.0)},
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
                    {
                        0: 1.0,
                        3: 0.7555555555555555,
                        4: 0.24444444444444444,
                        5: 1.0,
                        6: 0.66,
                    },
                    {
                        0: 1.0,
                        3: 0.7555555555555555,
                        4: 0.24444444444444444,
                        5: 0.66,
                        6: 0.43560000000000004,
                        7: 0.66,
                    },
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
                    {"bar": (0.0, 0.25, 1.0)},
                    {"bar": (0.25, 0.75, 1.0)},
                    {"bar": (0.75, 1.0, 1.0)},
                    {"foo": (0.0, 0.25, 1.0)},
                    {"foo": (0.25, 0.5, 1.0)},
                    {"foo": (0.5, 0.75, 1.0)},
                    {"foo": (0.75, 1.0, 1.0)},
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
                    {"bar": (0, 0.25, 1.0)},
                    {"bar": (0.25, 0.75, 1.0)},
                    {"bar": (0.75, 1.0, 1.0)},
                    {"foo": (0, 0.25, 1.0)},
                    {"foo": (0.25, 0.5, 1.0)},
                    {"foo": (0.5, 0.75, 1.0)},
                    {"foo": (0.75, 1.0, 1.0)},
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

    @pytest.mark.parametrize(
        "locations, axisOrder, masterValues, instanceLocation, expectedValue",
        [
            (
                [
                    {},
                    {"axis_A": 1.0},
                    {"axis_B": 1.0},
                    {"axis_A": 1.0, "axis_B": 1.0},
                    {"axis_A": 0.5, "axis_B": 1.0},
                    {"axis_A": 1.0, "axis_B": 0.5},
                ],
                ["axis_A", "axis_B"],
                [
                    0,
                    10,
                    20,
                    70,
                    50,
                    60,
                ],
                {
                    "axis_A": 0.5,
                    "axis_B": 0.5,
                },
                37.5,
            ),
        ],
    )
    def test_interpolation(
        self,
        locations,
        axisOrder,
        masterValues,
        instanceLocation,
        expectedValue,
    ):
        model = VariationModel(locations, axisOrder=axisOrder)
        interpolatedValue = model.interpolateFromMasters(instanceLocation, masterValues)

        assert interpolatedValue == expectedValue
