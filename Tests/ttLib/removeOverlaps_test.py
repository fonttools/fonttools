import logging
import pytest

pathops = pytest.importorskip("pathops")

from fontTools.ttLib.removeOverlaps import _simplify, _round_path


def test_pathops_simplify_bug_workaround(caplog):
    # Paths extracted from Noto Sans Ethiopic instance that fails skia-pathops
    # https://github.com/google/fonts/issues/3365
    # https://bugs.chromium.org/p/skia/issues/detail?id=11958
    path = pathops.Path()
    path.moveTo(550.461, 0)
    path.lineTo(550.461, 366.308)
    path.lineTo(713.229, 366.308)
    path.lineTo(713.229, 0)
    path.close()
    path.moveTo(574.46, 0)
    path.lineTo(574.46, 276.231)
    path.lineTo(737.768, 276.231)
    path.quadTo(820.075, 276.231, 859.806, 242.654)
    path.quadTo(899.537, 209.077, 899.537, 144.154)
    path.quadTo(899.537, 79, 853.46, 39.5)
    path.quadTo(807.383, 0, 712.383, 0)
    path.close()

    # check that it fails without workaround
    with pytest.raises(pathops.PathOpsError):
        pathops.simplify(path)

    # check our workaround works (but with a warning)
    with caplog.at_level(logging.DEBUG, logger="fontTools.ttLib.removeOverlaps"):
        result = _simplify(path, debugGlyphName="a")

    assert "skia-pathops failed to simplify 'a' with float coordinates" in caplog.text

    expected = pathops.Path()
    expected.moveTo(550, 0)
    expected.lineTo(550, 366)
    expected.lineTo(713, 366)
    expected.lineTo(713, 276)
    expected.lineTo(738, 276)
    expected.quadTo(820, 276, 860, 243)
    expected.quadTo(900, 209, 900, 144)
    expected.quadTo(900, 79, 853, 40)
    expected.quadTo(807.242, 0.211, 713, 0.001)
    expected.lineTo(713, 0)
    expected.close()

    assert expected == _round_path(result, round=lambda v: round(v, 3))
