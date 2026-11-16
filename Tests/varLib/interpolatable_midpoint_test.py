from math import sqrt

import pytest

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.lazyTools import LazyList
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.ttGlyphSet import LerpGlyphSet
from fontTools.varLib import interpolatable
from fontTools.varLib.models import VariationModel

SQUARE = [(0, 0), (100, 0), (100, 100), (0, 100)]
ROTATED = [(0, 0), (0, 100), (-100, 100), (-100, 0)]
MID_SQUARE = [(0, 0), (50, 50), (0, 100), (-50, 50)]


def polygon(points, count=1):
    pen = RecordingPen()
    for _ in range(count):
        pen.moveTo(points[0])
        for point in points[1:]:
            pen.lineTo(point)
        pen.closePath()
    return pen


def problems(glyphsets, kind, **kwargs):
    return [
        problem
        for _, problem in interpolatable.test_gen(glyphsets, **kwargs)
        if problem["type"] == kind
    ]


@pytest.mark.parametrize("scale, expected", [(sqrt(2), None), (1, 0.5), (0.5, 0.125)])
def test_underweight_actual_midpoint(scale, expected):
    glyphsets = [{"A": polygon(SQUARE)}, {"A": polygon(ROTATED)}]
    actual = polygon([(scale * x, scale * y) for x, y in MID_SQUARE])
    calls = []

    def midpoint(location):
        calls.append(location)
        return {"A": actual}

    result = problems(
        glyphsets,
        "underweight",
        locations=[{}, {"wght": 1}],
        midpointFunc=midpoint,
    )
    assert calls == [{"wght": 0.5}]
    if expected is None:
        assert result == []
    else:
        assert len(result) == 1
        assert result[0]["tolerance"] == pytest.approx(expected)
        assert result[0]["actual_midpoint"] is True


def test_actual_midpoint_drawn_once_for_multiple_findings():
    calls = []
    draws = []
    glyphsets = [{"A": polygon(SQUARE, 2)}, {"A": polygon(ROTATED, 2)}]

    class ActualGlyph:
        def draw(self, pen, **kwargs):
            draws.append(True)
            polygon(MID_SQUARE, 2).replay(pen)

    def midpoint(location):
        calls.append(location)
        return {"A": ActualGlyph()}

    result = problems(
        glyphsets,
        "underweight",
        locations=[{}, {"wght": 1}],
        midpointFunc=midpoint,
    )
    assert len(result) == 2
    assert calls == [{"wght": 0.5}]
    assert draws == [True]


def curve(previous, following, point=(0, 0)):
    pen = RecordingPen()
    pen.moveTo(point)
    pen.curveTo(following, (100, 100), (0, 100))
    pen.curveTo((-100, 100), previous, point)
    pen.closePath()
    return pen


@pytest.mark.parametrize("repaired", [False, True])
def test_kink_actual_midpoint(repaired):
    r = sqrt(0.5)
    previous0, following0 = (-30, 0), (70, 0)
    previous1, following1 = (-70 * r, -70 * r), (30 * r, 30 * r)
    glyphsets = [
        {"A": curve(previous0, following0)},
        {"A": curve(previous1, following1)},
    ]
    original = problems(glyphsets, "kink")
    assert len(original) == 1
    if repaired:
        previous = tuple((a + b) / 2 for a, b in zip(previous0, previous1))
        following = tuple((a + b) / 2 for a, b in zip(following0, following1))
        point = tuple((a + b) / 2 for a, b in zip(previous, following))
        actual = {"A": curve(previous, following, point)}
    else:
        actual = LerpGlyphSet(*glyphsets)
    calls = []

    def forbidden_name(index):
        pytest.fail("A suppressed finding must not resolve master names")

    def midpoint(location):
        calls.append(location)
        return actual

    result = problems(
        glyphsets,
        "kink",
        locations=[{}, {"wght": 1}],
        midpointFunc=midpoint,
        names=LazyList([forbidden_name] * 2) if repaired else None,
    )
    assert calls == [{"wght": 0.5}]
    if repaired:
        assert result == []
    else:
        assert len(result) == 1
        assert result[0]["tolerance"] == pytest.approx(original[0]["tolerance"])
        assert result[0]["actual_midpoint"] is True


def test_midpoint_not_evaluated_without_candidates(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("A successful check must not evaluate a midpoint or full moments")

    monkeypatch.setattr(interpolatable, "StatisticsPen", forbidden)
    monkeypatch.setattr(interpolatable, "StatisticsControlPen", forbidden)
    assert not list(
        interpolatable.test_gen(
            [{"A": polygon(SQUARE)}] * 2,
            locations=[{}, {"wght": 1}],
            names=LazyList([forbidden] * 2),
            midpointFunc=forbidden,
        )
    )


def test_midpoint_not_evaluated_for_structural_errors():
    def forbidden(*args):
        pytest.fail("A structural error needs no midpoint")

    result = problems(
        [{"A": polygon(SQUARE)}, {"A": polygon(SQUARE, 2)}],
        "path_count",
        locations=[{}, {"wght": 1}],
        midpointFunc=forbidden,
    )
    assert len(result) == 1


def test_midpoint_requires_locations():
    with pytest.raises(ValueError, match="requires master locations"):
        list(interpolatable.test_gen([], midpointFunc=lambda location: {}))


def test_unmatched_midpoint_retains_unconfirmed_finding():
    result = problems(
        [{"A": polygon(SQUARE)}, {"A": polygon(ROTATED)}],
        "underweight",
        locations=[{}, {"wght": 1}],
        midpointFunc=lambda location: {"A": polygon(SQUARE, 2)},
    )
    assert len(result) == 1
    assert "actual_midpoint" not in result[0]


@pytest.mark.parametrize("reverse", [False, True])
def test_underweight_detects_winding_reversal(reverse):
    points = SQUARE[::-1] if reverse else SQUARE
    transformed = [(-10 * x, -0.1 * y) for x, y in points]
    # Both endpoints have equal, matching signed areas. The midpoint has
    # twice their absolute area, but the opposite winding.
    result = problems(
        [{"A": polygon(points)}, {"A": polygon(transformed)}], "underweight"
    )
    assert len(result) == 1
    assert result[0]["tolerance"] == 0


@pytest.mark.parametrize("scale", [0.1, 1, 10])
def test_underweight_accepts_scaling(scale):
    assert not problems(
        [
            {"A": polygon(SQUARE)},
            {"A": polygon([(scale * x, scale * y) for x, y in SQUARE])},
        ],
        "underweight",
    )


def test_zero_kinkiness_disables_kink_check():
    r = sqrt(0.5)
    glyphsets = [
        {"A": curve((-30, 0), (70, 0))},
        {"A": curve((-70 * r, -70 * r), (30 * r, 30 * r))},
    ]
    assert not problems(glyphsets, "kink", kinkiness=0)


@pytest.mark.parametrize("jobs", [1, 2])
def test_gvar_midpoint_corrected_by_off_axis_master(tmp_path, jobs):
    locations = [
        {},
        {"wght": 0.75},
        {"wght": 0.75, "wdth": 1},
        {"wght": 0.5, "wdth": 0.5},
    ]
    model = VariationModel(locations)
    masters = [[(x + 10, y) for x, y in SQUARE], SQUARE, ROTATED]
    scalars = model.getMasterScalars({"wght": 0.75, "wdth": 0.5})
    desired = [(sqrt(2) * x, sqrt(2) * y) for x, y in MID_SQUARE]
    masters.append(
        [
            tuple(
                round(
                    (
                        target[axis]
                        - sum(s * m[i][axis] for s, m in zip(scalars, masters))
                    )
                    / scalars[3]
                )
                for axis in range(2)
            )
            for i, target in enumerate(desired)
        ]
    )

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({65: "A"})
    pen = TTGlyphPen(None)
    polygon(masters[0]).replay(pen)
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (500, 10)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Midpoint", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    fb.setupFvar([("wght", 0, 0, 1, "Weight"), ("wdth", 0, 0, 1, "Width")], [])
    deltas = model.getDeltas([GlyphCoordinates(points) for points in masters])
    fb.setupGvar(
        {
            ".notdef": [],
            "A": [
                TupleVariation(
                    support, [(round(x), round(y)) for x, y in delta] + [(0, 0)] * 4
                )
                for support, delta in zip(model.supports[1:], deltas[1:])
            ],
        }
    )
    font = fb.font

    def instance(location):
        return font.getGlyphSet(location=location, normalized=True, recalcBounds=False)

    glyphsets = [instance(location) for location in locations]
    pair_only = problems(glyphsets, "underweight", locations=locations)
    assert any(p["master_1_idx"] == 1 and p["master_2_idx"] == 2 for p in pair_only)
    confirmed = problems(
        glyphsets, "underweight", locations=locations, midpointFunc=instance
    )
    assert not any(p["master_1_idx"] == 1 and p["master_2_idx"] == 2 for p in confirmed)

    path = tmp_path / "midpoint.ttf"
    font.save(path)
    # Filtering the off-axis master out of the comparison tree must still
    # include its contribution when confirming the actual font instance.
    result = interpolatable.main(
        [
            "--quiet",
            "--jobs",
            str(jobs),
            "--glyphs",
            "A",
            "--name",
            "''",
            "--name",
            "'wght=0.75'",
            "--name",
            "'wdth=1.0 wght=0.75'",
            str(path),
        ]
    )
    assert not any(
        p["type"] == "underweight" for group in (result or {}).values() for p in group
    )
