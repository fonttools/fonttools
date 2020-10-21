from fontTools.misc.transform import Identity
from fontTools.pens.hashPointPen import HashPointPen
import pytest


class _TestGlyph(object):
    width = 500

    def drawPoints(self, pen):
        pen.beginPath(identifier="abc")
        pen.addPoint((0.0, 0.0), "line", False, "start", identifier="0000")
        pen.addPoint((10, 110), "line", False, None, identifier="0001")
        pen.addPoint((50.0, 75.0), None, False, None, identifier="0002")
        pen.addPoint((60.0, 50.0), None, False, None, identifier="0003")
        pen.addPoint((50.0, 0.0), "curve", True, "last", identifier="0004")
        pen.endPath()


class _TestGlyph2(_TestGlyph):
    def drawPoints(self, pen):
        pen.beginPath(identifier="abc")
        pen.addPoint((0.0, 0.0), "line", False, "start", identifier="0000")
        # Minor difference to _TestGlyph() is in the next line:
        pen.addPoint((101, 10), "line", False, None, identifier="0001")
        pen.addPoint((50.0, 75.0), None, False, None, identifier="0002")
        pen.addPoint((60.0, 50.0), None, False, None, identifier="0003")
        pen.addPoint((50.0, 0.0), "curve", True, "last", identifier="0004")
        pen.endPath()


class _TestGlyph3(_TestGlyph):
    def drawPoints(self, pen):
        pen.beginPath(identifier="abc")
        pen.addPoint((0.0, 0.0), "line", False, "start", identifier="0000")
        pen.addPoint((10, 110), "line", False, None, identifier="0001")
        pen.endPath()
        # Same segment, but in a different path:
        pen.beginPath(identifier="pth2")
        pen.addPoint((50.0, 75.0), None, False, None, identifier="0002")
        pen.addPoint((60.0, 50.0), None, False, None, identifier="0003")
        pen.addPoint((50.0, 0.0), "curve", True, "last", identifier="0004")
        pen.endPath()


class _TestGlyph4(_TestGlyph):
    def drawPoints(self, pen):
        pen.beginPath(identifier="abc")
        pen.addPoint((0.0, 0.0), "move", False, "start", identifier="0000")
        pen.addPoint((10, 110), "line", False, None, identifier="0001")
        pen.addPoint((50.0, 75.0), None, False, None, identifier="0002")
        pen.addPoint((60.0, 50.0), None, False, None, identifier="0003")
        pen.addPoint((50.0, 0.0), "curve", True, "last", identifier="0004")
        pen.endPath()


class _TestGlyph5(_TestGlyph):
    def drawPoints(self, pen):
        pen.addComponent("b", Identity)


class HashPointPenTest(object):
    def test_addComponent(self):
        pen = HashPointPen(_TestGlyph().width, {"a": _TestGlyph()})
        pen.addComponent("a", (2, 0, 0, 3, -10, 5))
        assert pen.hash == "w500[l0+0l10+110o50+75o60+50c50+0|(+2+0+0+3-10+5)]"

    def test_NestedComponents(self):
        pen = HashPointPen(
            _TestGlyph().width, {"a": _TestGlyph5(), "b": _TestGlyph()}
        )  # "a" contains "b" as a component
        pen.addComponent("a", (2, 0, 0, 3, -10, 5))

        assert (
            pen.hash
            == "w500[[l0+0l10+110o50+75o60+50c50+0|(+1+0+0+1+0+0)](+2+0+0+3-10+5)]"
        )

    def test_outlineAndComponent(self):
        pen = HashPointPen(_TestGlyph().width, {"a": _TestGlyph()})
        glyph = _TestGlyph()
        glyph.drawPoints(pen)
        pen.addComponent("a", (2, 0, 0, 2, -10, 5))

        assert (
            pen.hash
            == "w500l0+0l10+110o50+75o60+50c50+0|[l0+0l10+110o50+75o60+50c50+0|(+2+0+0+2-10+5)]"
        )

    def test_addComponent_missing_raises(self):
        pen = HashPointPen(_TestGlyph().width, dict())
        with pytest.raises(KeyError) as excinfo:
            pen.addComponent("a", Identity)
        assert excinfo.value.args[0] == "a"

    def test_similarGlyphs(self):
        pen = HashPointPen(_TestGlyph().width)
        glyph = _TestGlyph()
        glyph.drawPoints(pen)

        pen2 = HashPointPen(_TestGlyph2().width)
        glyph = _TestGlyph2()
        glyph.drawPoints(pen2)

        assert pen.hash != pen2.hash

    def test_similarGlyphs2(self):
        pen = HashPointPen(_TestGlyph().width)
        glyph = _TestGlyph()
        glyph.drawPoints(pen)

        pen2 = HashPointPen(_TestGlyph3().width)
        glyph = _TestGlyph3()
        glyph.drawPoints(pen2)

        assert pen.hash != pen2.hash

    def test_similarGlyphs3(self):
        pen = HashPointPen(_TestGlyph().width)
        glyph = _TestGlyph()
        glyph.drawPoints(pen)

        pen2 = HashPointPen(_TestGlyph4().width)
        glyph = _TestGlyph4()
        glyph.drawPoints(pen2)

        assert pen.hash != pen2.hash

    def test_glyphVsComposite(self):
        # If a glyph contains a component, the decomposed glyph should still
        # compare false
        pen = HashPointPen(_TestGlyph().width, {"a": _TestGlyph()})
        pen.addComponent("a", Identity)

        pen2 = HashPointPen(_TestGlyph().width)
        glyph = _TestGlyph()
        glyph.drawPoints(pen2)

        assert pen.hash != pen2.hash
