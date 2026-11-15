from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import builder
from fontTools.varLib.avar.map import ForwardMapper, _denormalize, main, map as map_avar
from fontTools.varLib.models import normalizeValue
from pathlib import Path
import pytest


@pytest.fixture(params=[None, 1, 2], ids=["no-avar", "avar1", "avar2"])
def font(request):
    font = TTFont()
    font["fvar"] = newTable("fvar")
    for tag, triple in (("wght", (100, 400, 900)), ("wdth", (50, 100, 125))):
        axis = Axis()
        axis.axisTag = tag
        axis.minValue, axis.defaultValue, axis.maxValue = triple
        axis.axisNameID = 256
        font["fvar"].axes.append(axis)
    if request.param is not None:
        avar = font["avar"] = newTable("avar")
        avar.majorVersion = request.param
        avar.segments = {
            "wght": {-1: -1, 0: 0, 0.5: 0.75, 1: 1},
            "wdth": {-1: -1, 0: 0, 1: 1},
        }
        if request.param == 2:
            avar.table = otTables.avar()
            avar.table.VarIdxMap = None
            avar.table.VarStore = builder.buildVarStore(
                builder.buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"]),
                [builder.buildVarData([0], [[0], [4096]])],
            )
    return font


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("output_normalized", [False, True])
@pytest.mark.parametrize("drop_zeroes", [False, True])
def test_empty_location_uses_defaults(
    font, input_normalized, output_normalized, drop_zeroes
):
    expected = (
        {}
        if drop_zeroes
        else (
            {"wght": 0, "wdth": 0} if output_normalized else {"wght": 400, "wdth": 100}
        )
    )
    result = map_avar(
        font,
        {},
        inputNormalized=input_normalized,
        outputNormalized=output_normalized,
        dropZeroes=drop_zeroes,
    )
    assert result == expected


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("drop_zeroes", [False, True])
def test_sparse_location_uses_defaults(font, input_normalized, drop_zeroes):
    has_avar = "avar" in font
    avar2 = has_avar and font["avar"].majorVersion == 2
    expected = {"wght": 0.75 if has_avar else 0.5, "wdth": 0.1875 if avar2 else 0}
    if drop_zeroes:
        expected = {tag: v for tag, v in expected.items() if v != 0}
    assert (
        map_avar(
            font,
            {"wght": 0.5 if input_normalized else 650},
            inputNormalized=input_normalized,
            outputNormalized=True,
            dropZeroes=drop_zeroes,
        )
        == expected
    )


@pytest.mark.parametrize("input_normalized", [False, True])
def test_explicit_defaults_are_omitted(font, input_normalized):
    location = (
        {"wght": 0, "wdth": 0} if input_normalized else {"wght": 400, "wdth": 100}
    )
    assert (
        map_avar(font, location, inputNormalized=input_normalized, dropZeroes=True)
        == {}
    )


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize(
    "flags,expected",
    [
        ([], {}),
        (["-f"], {"wght": 400, "wdth": 100}),
        (["-f", "-o"], {"wght": 0, "wdth": 0}),
    ],
)
def test_cli_accepts_empty_location(
    font, tmp_path, capsys, input_normalized, flags, expected
):
    path = tmp_path / "test.ttf"
    font.save(path)
    main([*flags, *(["-i"] if input_normalized else []), str(path)])
    output = capsys.readouterr()
    actual = {
        tag: float(value)
        for tag, value in (line.split("=") for line in output.out.splitlines())
    }
    assert actual == expected
    assert output.err == ""


def test_default_location_applies_avar2_bias():
    font = TTFont()
    font["fvar"] = newTable("fvar")
    axis = Axis()
    axis.axisTag = "wght"
    axis.minValue, axis.defaultValue, axis.maxValue = 100, 400, 900
    font["fvar"].axes = [axis]
    avar = font["avar"] = newTable("avar")
    avar.majorVersion = 2
    avar.segments = {"wght": {-1: -1, 0: 0, 1: 1}}
    avar.table = otTables.avar()
    avar.table.VarIdxMap = None
    avar.table.VarStore = builder.buildVarStore(
        builder.buildVarRegionList([{}], ["wght"]),
        [builder.buildVarData([0], [[4096]])],
    )
    # A constant avar2 bias can move the default. Empty input must still go
    # through avar instead of returning early or unconditionally dropping axes.
    for normalized in (False, True):
        assert map_avar(
            font, {}, inputNormalized=normalized, outputNormalized=True, dropZeroes=True
        ) == {"wght": 0.25}


def reference_map(
    font, location, *, inputNormalized=False, outputNormalized=False, dropZeroes=False
):
    triples = {
        a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes
    }
    normalized = {
        tag: (
            location.get(tag, 0)
            if inputNormalized
            else normalizeValue(location.get(tag, triple[1]), triple)
        )
        for tag, triple in triples.items()
    }
    if "avar" in font:
        normalized = font["avar"].renormalizeLocation(
            normalized, font, dropZeroes=False
        )
    return {
        tag: value if outputNormalized else _denormalize(value, triples[tag])
        for tag, value in normalized.items()
        if not dropZeroes or value != 0
    }


@pytest.mark.parametrize("input_normalized", [False, True])
@pytest.mark.parametrize("output_normalized", [False, True])
@pytest.mark.parametrize("drop_zeroes", [False, True])
def test_prepared_mapper_matches_table_across_locations(
    font, input_normalized, output_normalized, drop_zeroes
):
    mapper = ForwardMapper(font)
    locations = (
        [{"wght": 1, "wdth": 1}, {"wght": -1}, {"wght": 0.5}, {}, {"wdth": -0.25}]
        if input_normalized
        else [
            {"wght": 900, "wdth": 125},
            {"wght": 100},
            {"wght": 650},
            {},
            {"wdth": 87.5},
        ]
    )
    options = dict(
        inputNormalized=input_normalized,
        outputNormalized=output_normalized,
        dropZeroes=drop_zeroes,
    )
    for location in locations:
        assert mapper.map(location, **options) == reference_map(
            font, location, **options
        )


def test_prepared_mapper_keeps_support_cache():
    path = Path(__file__).parent.parent / "ttLib/tables/data/Amstelvar-avar2.subset.ttf"
    mapper = ForwardMapper(TTFont(path))
    mapper.map({"wght": 700}, outputNormalized=True)
    supports = dict(mapper._instancer._supports)
    assert supports
    mapper.map({"wdth": 75}, outputNormalized=True)
    assert all(
        mapper._instancer._supports[i] is support for i, support in supports.items()
    )


@pytest.mark.parametrize("indices", [None, [0, 0], [0xFFFFFFFF, 0x12345678], [0]])
def test_prepared_mapper_avar2_indices(indices):
    font = TTFont()
    font["fvar"] = newTable("fvar")
    for tag in ("wght", "wdth"):
        axis = Axis()
        axis.axisTag = tag
        axis.minValue, axis.defaultValue, axis.maxValue = 100, 400, 900
        font["fvar"].axes.append(axis)
    avar = font["avar"] = newTable("avar")
    avar.majorVersion = 2
    avar.segments = {tag: {-1: -1, 0: 0, 1: 1} for tag in ("wght", "wdth")}
    avar.table = otTables.avar()
    avar.table.VarIdxMap = (
        builder.buildDeltaSetIndexMap(indices) if indices is not None else None
    )
    avar.table.VarStore = builder.buildVarStore(
        builder.buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"]),
        [builder.buildVarData([0], [[1], [32768]])],
    )
    mapper = ForwardMapper(font)
    for location in ({"wght": 0.5}, {"wght": 1}, {}, {"wdth": -1}):
        assert mapper.map(
            location, inputNormalized=True, outputNormalized=True
        ) == reference_map(font, location, inputNormalized=True, outputNormalized=True)
    # A NULL store still quantizes the identity term but does not clamp it.
    avar.table.VarStore = None
    mapper = ForwardMapper(font)
    for location in ({"wght": 0.5 / 16384}, {"wght": 2.5}):
        assert mapper.map(
            location, inputNormalized=True, outputNormalized=True
        ) == reference_map(font, location, inputNormalized=True, outputNormalized=True)


def test_prepared_mapper_requires_fvar():
    with pytest.raises(ValueError, match="fvar"):
        ForwardMapper(TTFont())
    assert map_avar(TTFont(), {}) is None


def test_prepared_mapper_rejects_unknown_axes(font):
    with pytest.raises(ValueError, match="Unknown axis"):
        ForwardMapper(font).map({"XXXX": 0})


def test_packed_scorer_matches_forward(font):
    pytest.importorskip("numpy")
    from fontTools.varLib.avar._scorer import _ForwardScorer

    forward = ForwardMapper(font)
    score = _ForwardScorer(forward)
    locations = [
        {},
        {"wght": 100},
        {"wght": 900, "wdth": 125},
        {"wght": -100, "wdth": 999},
    ]
    for i in range(65):
        locations.append(
            {"wght": 100 + 800 * i / 64, "wdth": 50 + 75 * ((i * 17) % 65) / 64}
        )
    for location in locations:
        assert score(location) == forward.map(location, outputNormalized=True)


@pytest.mark.parametrize("pinned", [{}, {"wdth": 100.1}])
def test_batch_scorer_matches_scalar_roundtrip(font, pinned):
    np = pytest.importorskip("numpy")
    from fontTools.varLib.avar._scorer import _ForwardScorer

    forward = ForwardMapper(font)
    score = _ForwardScorer(forward, pinned=pinned)
    coordinates = np.random.default_rng(0).uniform(-1, 1, (30, len(forward.tags)))
    actual = score.batch(coordinates)
    for values, output in zip(coordinates, actual):
        user = {
            tag: _denormalize(v, forward.triples[tag])
            for tag, v in zip(forward.tags, values)
        }
        user.update(pinned)
        expected = forward.map(user, outputNormalized=True)
        np.testing.assert_array_equal(output, [expected[tag] for tag in forward.tags])


@pytest.mark.parametrize("variant", ["normal", "null", "indices", "duplicate"])
def test_packed_scorer_rounding_and_row_order(variant):
    pytest.importorskip("numpy")
    from fontTools.varLib.avar._scorer import _ForwardScorer

    font = TTFont(
        Path(__file__).parent.parent / "ttLib/tables/data/Amstelvar-avar2.subset.ttf"
    )
    avar = font["avar"].table
    if variant == "null":
        avar.VarStore = None
    elif variant == "indices":
        avar.VarIdxMap = builder.buildDeltaSetIndexMap([0xFFFFFFFF, 0x12345678, 0, 0])
    elif variant == "duplicate":
        for data in avar.VarStore.VarData:
            data.VarRegionIndex = data.VarRegionIndex[::-1] * 2
            data.Item = [row[::-1] * 2 for row in data.Item]
    forward = ForwardMapper(font)
    score = _ForwardScorer(forward)
    # Include half-tick positions and both sides of support boundaries.
    for i in range(33):
        location = {
            tag: _denormalize((i - 16.5) / 32, triple)
            for tag, triple in forward.triples.items()
        }
        assert score(location) == forward.map(location, outputNormalized=True)
