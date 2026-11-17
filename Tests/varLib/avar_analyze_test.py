import json

import pytest

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import builder
from fontTools.varLib.avar.analyze import analyze, contours, main
from fontTools.varLib.avar.map import ForwardMapper


def make_font(supports=None, deltas=None, segments=None):
    font = TTFont()
    font["fvar"] = newTable("fvar")
    for tag in ("wght", "wdth", "priv"):
        axis = Axis()
        axis.axisTag = tag
        axis.minValue, axis.defaultValue, axis.maxValue = -1, 0, 1
        axis.flags = int(tag == "priv")
        axis.axisNameID = 256
        font["fvar"].axes.append(axis)
    if supports is not None or segments is not None:
        avar = font["avar"] = newTable("avar")
        avar.majorVersion = 2 if supports is not None else 1
        avar.segments = {tag: {-1: -1, 0: 0, 1: 1} for tag in ("wght", "wdth", "priv")}
        avar.segments.update(segments or {})
        if supports is not None:
            avar.table = otTables.avar()
            avar.table.VarIdxMap = None
            avar.table.VarStore = builder.buildVarStore(
                builder.buildVarRegionList(supports, ["wght", "wdth", "priv"]),
                [
                    builder.buildVarData(
                        range(len(supports)),
                        [
                            [
                                round(v * 16384)
                                for v in (deltas or {}).get(tag, [0] * len(supports))
                            ]
                            for tag in ("wght", "wdth", "priv")
                        ],
                    )
                ],
            )
    return font


def test_identity():
    result = analyze(make_font())
    assert list(result["axes"]) == ["wght", "wdth"]
    assert result["fixed"] == {"priv": 0}
    assert result["boundaries"] == result["regions"] == []
    assert result["outputBounds"] == {"wght": [-1, 1], "wdth": [-1, 1], "priv": [0, 0]}


def test_analyze_needs_no_optional_dependencies(monkeypatch):
    import sys

    for module in ("numpy", "scipy", "contourpy"):
        monkeypatch.setitem(sys.modules, module, None)
    assert analyze(make_font())["fixed"] == {"priv": 0}


def test_hidden_input_disables_region_but_hidden_output_is_retained():
    font = make_font(
        [{"priv": (0, 1, 1)}, {"wght": (0, 0.5, 1), "wdth": (-1, -0.5, 0)}],
        {"priv": [1, 1]},
    )
    result = analyze(font)
    assert [r["index"] for r in result["regions"]] == [1]
    assert result["regions"][0]["interaction"]
    assert result["regions"][0]["ranges"] == {"wght": [[0, 1]], "wdth": [[-1, 0]]}
    assert result["regions"][0]["outputs"] == {"priv": 1}
    assert len(result["boundaries"]) == 6


def test_segment_and_region_preimages_in_user_units():
    font = make_font(
        [{"wght": (0, 0.5, 1)}],
        {"priv": [1]},
        {"wght": {-1: -1, 0: 0, 0.25: 0.5, 0.5: 0.5, 1: 1}},
    )
    axis = font["fvar"].axes[0]
    axis.minValue, axis.defaultValue, axis.maxValue = 100, 400, 900
    result = analyze(font)
    peaks = [
        b["value"]
        for b in result["boundaries"]
        if b["kind"] == "region" and "peak" in b["roles"]
    ]
    assert peaks == [525, 650]
    assert result["regions"][0]["ranges"] == {"wght": [[400, 900]]}
    assert {b["value"] for b in result["boundaries"] if b["kind"] == "segment"} == {
        400,
        525,
        650,
    }


def test_plateau_preimage_of_zero_width_support():
    font = make_font(
        [{"wght": (0.5, 0.5, 0.5)}],
        {"priv": [1]},
        {"wght": {-1: -1, 0: 0, 0.25: 0.5, 0.5: 0.5, 1: 1}},
    )
    assert analyze(font)["regions"][0]["ranges"] == {"wght": [[0.25, 0.5]]}


@pytest.mark.parametrize("variant", ["null", "invalid", "shared", "truncated"])
def test_varstore_indices(variant):
    font = make_font([{"wght": (0, 1, 1)}], {"wght": [0.25], "priv": [0.5]})
    table = font["avar"].table
    if variant == "null":
        table.VarStore = None
    elif variant == "invalid":
        table.VarIdxMap = builder.buildDeltaSetIndexMap([0xFFFFFFFF] * 3)
    elif variant == "shared":
        table.VarIdxMap = builder.buildDeltaSetIndexMap([2, 2, 2])
    else:
        table.VarIdxMap = builder.buildDeltaSetIndexMap([2])
    result = analyze(font)
    assert bool(result["regions"]) == (variant in ("shared", "truncated"))
    if variant == "shared":
        assert result["regions"][0]["outputs"] == {
            "wght": 0.5,
            "wdth": 0.5,
            "priv": 0.5,
        }
    elif variant == "truncated":
        assert result["regions"][0]["outputs"] == {"wght": 0.5}


def test_bounds_cover_rounded_clipped_outputs():
    font = make_font(
        [
            {},
            {"wght": (0, 0.5, 1)},
            {"wght": (-1, -0.5, 0), "wdth": (0, 1, 1)},
            {"priv": (0, 1, 1)},
        ],
        {"wght": [0.1, 0.75, -0.5, 1], "priv": [0.25, -0.5, 1, 1]},
    )
    bounds = analyze(font)["outputBounds"]
    mapper = ForwardMapper(font)
    for x in (-1, -0.5, 0, 0.25, 0.5, 0.75, 1):
        for y in (-1, 0, 0.5, 1):
            actual = mapper.map({"wght": x, "wdth": y}, outputNormalized=True)
            for tag, value in actual.items():
                assert bounds[tag][0] <= value <= bounds[tag][1]


def test_constant_bias_bounds_clamp_both_ends():
    font = make_font([{}], {"priv": [2]})
    assert analyze(font)["outputBounds"]["priv"] == [1, 1]


def test_analyze_cli(tmp_path, capsys):
    path = tmp_path / "font.ttf"
    make_font().save(path)
    main([str(path)])
    assert json.loads(capsys.readouterr().out)["fixed"] == {"priv": 0}


def test_one_axis_contours_and_plateaus():
    pytest.importorskip("scipy")
    font = make_font([{"wght": (0, 0.5, 1)}], {"priv": [1]})
    result = contours(font, ["wght"], "priv", 0.25, samples=2)
    assert [p[0] for p in result["points"]] == pytest.approx([0.125, 0.875])
    assert result["lines"] == []
    result = contours(font, ["wght"], "priv", 0, samples=2)
    assert result["lines"] == [[[-1], [0]]]
    assert result["points"] == [[1]]


def test_two_axis_hyperbola():
    pytest.importorskip("contourpy")
    font = make_font([{"wght": (0, 1, 1), "wdth": (0, 1, 1)}], {"priv": [1]})
    result = contours(font, ["wght", "wdth"], "priv", 0.25, samples=17)
    assert len(result["lines"]) == 1
    assert result["approximate"]
    for x, y in result["lines"][0]:
        assert x * y == pytest.approx(0.25)
    assert result["fixed"] == {"priv": 0}


def test_two_axis_isolated_maximum():
    pytest.importorskip("contourpy")
    font = make_font([{"wght": (0, 0.5, 1), "wdth": (0, 0.5, 1)}], {"priv": [1]})
    result = contours(font, ["wght", "wdth"], "priv", 1, samples=3)
    assert result["points"] == [[0.5, 0.5]]
    assert result["lines"] == result["boxes"] == []


@pytest.mark.parametrize("peak", [0.5, 1])
def test_contours_reject_jumps_including_domain_edge(peak):
    font = make_font([{"wght": (peak, peak, peak)}], {"priv": [1]})
    with pytest.raises(ValueError, match="jump"):
        contours(font, ["wght"], "priv", 0.5)


@pytest.mark.parametrize(
    "axes,kwargs,match",
    [
        (["priv"], {}, "non-hidden"),
        (["wght", "wght"], {}, "distinct"),
        (["wght"], {"location": {"priv": 0.5}}, "default"),
        (["wght"], {"location": {"wght": 0.5}}, "fix slice"),
        (["wght", "wdth"], {"samples": 1000}, "65536"),
    ],
)
def test_slice_validation(axes, kwargs, match):
    with pytest.raises(ValueError, match=match):
        contours(make_font(), axes, "priv", **kwargs)
