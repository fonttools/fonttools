import pytest

matplotlib = pytest.importorskip("matplotlib")
pytest.importorskip("contourpy")
matplotlib.use("Agg")

from matplotlib import pyplot
from fontTools.varLib.avar.plot import plot, main, _boundaryLines
from .avar_analyze_test import make_font


def test_plot_uses_analyzer_and_contour_geometry(monkeypatch):
    from fontTools.varLib.avar import plot as module

    font = make_font([{"wght": (0, 1, 1), "wdth": (0, 1, 1)}], {"priv": [1]})
    analyze_calls, contour_calls = [], []
    original_analyze, original_contours = module.analyze, module.contours

    def analyzed(font):
        result = original_analyze(font)
        analyze_calls.append(result)
        return result

    def contoured(*args, **kwargs):
        result = original_contours(*args, **kwargs)
        contour_calls.append(result)
        return result

    monkeypatch.setattr(module, "analyze", analyzed)
    monkeypatch.setattr(module, "contours", contoured)
    figure = plot(font, ["wght", "wdth"], output="priv", levels=[0.25], samples=9)
    assert len(analyze_calls) == 1
    assert contour_calls[-1]["level"] == 0.25
    assert len(contour_calls[-1]["lines"]) == 1
    assert len(figure.axes) == 3  # two views and a shared colorbar
    # Verify the plotted curve is the actual contour API result.
    lines = figure.axes[0].collections[2].get_segments()
    import numpy as np

    np.testing.assert_allclose(lines[0], contour_calls[-1]["lines"][0])
    figure.canvas.draw()
    pyplot.close(figure)


def test_boundary_patches_are_intersected_with_slice():
    report = dict(
        axes={
            t: dict(minimum=-1, default=0, maximum=1) for t in ("wght", "wdth", "opsz")
        },
        boundaries=[
            dict(
                axis="wght",
                value=0.5,
                ranges={"opsz": [[0.5, 1]], "wdth": [[0.25, 0.75]]},
            )
        ],
    )
    assert _boundaryLines(report, ["wght", "wdth"], {}) == []
    assert _boundaryLines(report, ["wght", "wdth"], {"opsz": 0.75}) == [
        ((0.5, 0.25), (0.5, 0.75))
    ]


def test_plot_cli_saves_figure(tmp_path):
    pytest.importorskip("scipy")
    path = tmp_path / "font.ttf"
    destination = tmp_path / "plot.svg"
    make_font([{"wght": (0, 0.5, 1)}], {"priv": [1]}).save(path)
    main([str(path), "wght", "--output", "priv", "-o", str(destination)])
    assert "<svg" in destination.read_text()
    pyplot.close("all")


def test_plot_rejects_jumps_in_projected_output():
    # The color output is continuous, but the other projected coordinate
    # jumps. Connecting adjacent grid samples would invent image points.
    font = make_font([{"wght": (0.5, 0.5, 0.5)}], {"wght": [0.25]})
    with pytest.raises(ValueError, match="jump"):
        plot(font, ["wght", "wdth"], output="priv", samples=3)
