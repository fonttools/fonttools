import json

import pytest

from fontTools.varLib.avar.reachability import ReachabilityMapper, check, main
from .avar_analyze_test import make_font


def test_bounds_prove_unreachable_without_scipy(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "scipy", None)
    result = check(make_font(), {"priv": 0.5}, inputNormalized=True)
    assert result["status"] == "unreachable"
    assert result["errorLowerBound"] == 0.5
    assert result["input"] is None


def test_out_of_range_target_is_not_clamped():
    result = check(make_font(), {"wght": 2})
    assert result["status"] == "unreachable"
    assert result["target"] == {"wght": 2}


def test_empty_target_and_default_need_no_scipy(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "scipy", None)
    for target in ({}, {"wght": 0}):
        result = check(make_font(), target, inputNormalized=True)
        assert result["status"] == "reachable"
        assert result["input"] == {}


def test_tolerance_near_output_cube_boundary():
    pytest.importorskip("scipy")
    result = check(make_font(), {"wght": 1.1}, inputNormalized=True, tolerance=0.11)
    assert result["status"] == "reachable"
    assert result["error"] == pytest.approx(0.1)


def test_hidden_output_target_leaves_omitted_outputs_free():
    pytest.importorskip("scipy")
    font = make_font([{"wght": (0, 1, 1)}], {"priv": [1]})
    mapper = ReachabilityMapper(font)
    for value in (0.25, 0.75, 0.25):
        result = mapper.check({"priv": value}, inputNormalized=True)
        assert result["status"] == "reachable"
        assert "priv" not in result["input"]
        assert "wdth" not in result["input"]
        assert result["input"]["wght"] == pytest.approx(value)
        assert result["output"]["priv"] == value
        assert result["error"] == 0


def test_joint_infeasibility_is_not_claimed_from_marginal_bounds():
    pytest.importorskip("scipy")
    font = make_font([{"wght": (0, 1, 1)}], {"priv": [1]})
    result = check(font, {"wght": 0.75, "priv": 0.25}, inputNormalized=True)
    assert result["status"] == "undetermined"
    assert result["error"] > 0.3
    assert result["errorLowerBound"] == 0
    assert "priv" not in result["input"]


def test_witness_omits_nonzero_defaults():
    pytest.importorskip("scipy")
    from fontTools.varLib.avar.map import ForwardMapper

    font = make_font()
    for axis in font["fvar"].axes:
        axis.minValue, axis.defaultValue, axis.maxValue = 100, 400, 900
    result = check(font, {"wght": 0.5}, inputNormalized=True)
    assert result["status"] == "reachable"
    assert result["input"] == {"wght": 650}
    assert (
        ForwardMapper(font).map(result["input"], outputNormalized=True)
        == result["output"]
    )


def test_partial_reverse_cache_distinguishes_scored_axes():
    pytest.importorskip("scipy")
    from fontTools.varLib.avar.reverse import ReverseMapper

    mapper = ReverseMapper(make_font([{"wght": (0, 1, 1)}], {"priv": [1]}))
    _, constrained_error = mapper.reverse({"priv": 0.5}, inputNormalized=True)
    witness, partial_error = mapper.reverse(
        {"priv": 0.5}, inputNormalized=True, partial=True
    )
    assert constrained_error > 0.3
    assert partial_error == 0
    assert witness["wght"] == pytest.approx(0.5)


def test_cli(tmp_path, capsys):
    pytest.importorskip("scipy")
    path = tmp_path / "font.ttf"
    make_font([{"wght": (0, 1, 1)}], {"priv": [1]}).save(path)
    main(["-i", str(path), "priv=0.5"])
    assert json.loads(capsys.readouterr().out)["status"] == "reachable"
