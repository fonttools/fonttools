from types import SimpleNamespace

import pytest

from fontTools.misc.transform import Identity
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.pens.statisticsPen import StatisticsPen, StatisticsControlPen
from fontTools.varLib import interpolatable
from fontTools.varLib.interpolatableHelpers import contour_vector_from_stats


def component(name, transform=Identity):
    pen = RecordingPen()
    pen.addComponent(name, transform)
    return pen


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    "transform",
    [
        Identity,
        (-1, 0, 0, 1, 80, 25),
        (0.75, 0.25, -0.125, 1.5, 10, -30),
        (1, 2, 2, 4, -10, 20),
    ],
)
def test_component_statistics_reuse(nested, transform):
    outline = RecordingPen()
    outline.moveTo((0, 0))
    outline.qCurveTo((50, 125), (100, 0))
    outline.lineTo((120, -20))
    outline.curveTo((80, -50), (20, -30), (0, 0))
    outline.closePath()
    outline.moveTo((150, 0))
    outline.lineTo((180, 60))
    outline.lineTo((200, 0))
    outline.closePath()
    draws = []

    def draw(pen):
        draws.append(True)
        outline.replay(pen)

    composite = component("nested" if nested else "base", transform)
    composite.addComponent("base", (0.5, 0, 0, 0.5, 200, 50))
    glyphset = {
        "base": SimpleNamespace(draw=draw),
        "nested": component("base", (1.25, 0.125, -0.25, 0.75, 40, -20)),
        "composite": composite,
    }
    expected = []
    for entry in composite.value:
        pens = [
            AreaPen(glyphset),
            StatisticsPen(glyphset),
            StatisticsControlPen(glyphset),
        ]
        for pen in pens:
            replayRecording([entry], pen)
        expected.append(pens)
    draws.clear()

    glyph = interpolatable.Glyph("composite", glyphset)
    assert len(draws) == 2
    assert glyph.nodeTypes == [["addComponent"], ["addComponent"]]
    assert [recording.value for recording in glyph.recordings] == [
        [entry] for entry in composite.value
    ]
    assert glyph.points == [None, None]
    assert list(glyph.isomorphisms) == [None, None]
    fields = (
        "area",
        "meanX",
        "meanY",
        "varianceX",
        "varianceY",
        "stddevX",
        "stddevY",
        "covariance",
        "correlation",
        "slant",
    )
    for i, (area, green, control) in enumerate(expected):
        assert glyph.areas[i] == area.value
        for actual, reference in [
            (glyph.greenStats[i], green),
            (glyph.controlStats[i], control),
        ]:
            assert [getattr(actual, field) for field in fields] == [
                getattr(reference, field) for field in fields
            ]
        assert glyph.greenVectors[i] == contour_vector_from_stats(green)
        assert glyph.controlVectors[i] == contour_vector_from_stats(control)
    assert len(draws) == 2


def test_missing_component_is_skipped(caplog):
    glyph = interpolatable.Glyph("composite", {"composite": component("missing")})
    assert glyph.areas == [0]
    assert glyph.greenStats[0].area == 0
    assert glyph.controlStats[0].area == 0
    assert "missing from glyphSet; skipped" in caplog.text


def test_open_component_is_reported():
    outline = RecordingPen()
    outline.moveTo((0, 0))
    outline.lineTo((100, 0))
    outline.endPath()
    glyphset = {"base": outline, "composite": component("base")}
    problems = list(
        interpolatable.test_gen(
            [glyphset, glyphset], glyphs=["composite"], names=["Regular", "Bold"]
        )
    )
    assert problems == [
        (
            "composite",
            {"type": "open_path", "master": name, "master_idx": i, "contour": 0},
        )
        for i, name in enumerate(["Regular", "Bold"])
    ]


@pytest.mark.parametrize("error", [ValueError, NotImplementedError])
def test_unsupported_component_is_open(error):
    def draw(pen):
        raise error

    glyphset = {"base": SimpleNamespace(draw=draw), "composite": component("base")}
    glyph = interpolatable.Glyph("composite", glyphset)
    assert glyph.openContours == [True]
    assert glyph.areas == [None]
    assert list(glyph.greenStats) == [None]
    assert list(glyph.controlStats) == [None]
