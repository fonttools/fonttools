import os
import pytest
import struct

from fontTools import ttLib
from fontTools.pens.basePen import PenError
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen
from fontTools.pens.ttGlyphPen import TTGlyphPen, TTGlyphPointPen, MAX_F2DOT14


class TTGlyphPenTestBase:
    def runEndToEnd(self, filename):
        font = ttLib.TTFont()
        ttx_path = os.path.join(
            os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
            "..",
            "ttLib",
            "data",
            filename,
        )
        font.importXML(ttx_path)

        glyphSet = font.getGlyphSet()
        glyfTable = font["glyf"]
        pen = self.penClass(glyphSet)

        for name in font.getGlyphOrder():
            getattr(glyphSet[name], self.drawMethod)(pen)
            oldGlyph = glyfTable[name]
            newGlyph = pen.glyph()

            if hasattr(oldGlyph, "program"):
                newGlyph.program = oldGlyph.program

            assert oldGlyph.compile(glyfTable) == newGlyph.compile(glyfTable)

    def test_e2e_linesAndSimpleComponents(self):
        self.runEndToEnd("TestTTF-Regular.ttx")

    def test_e2e_curvesAndComponentTransforms(self):
        self.runEndToEnd("TestTTFComplex-Regular.ttx")


class TTGlyphPenTest(TTGlyphPenTestBase):
    penClass = TTGlyphPen
    drawMethod = "draw"

    def test_moveTo_errorWithinContour(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        with pytest.raises(PenError):
            pen.moveTo((1, 0))

    def test_closePath_ignoresAnchors(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.closePath()
        assert not pen.points
        assert not pen.types
        assert not pen.endPts

    def test_endPath_sameAsClosePath(self):
        pen = TTGlyphPen(None)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        closePathGlyph = pen.glyph()

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.endPath()
        endPathGlyph = pen.glyph()

        assert closePathGlyph == endPathGlyph

    def test_glyph_errorOnUnendedContour(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        with pytest.raises(PenError):
            pen.glyph()

    def test_glyph_decomposes(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        pen.addComponent(componentName, (1, 0, 0, 1, 2, 0))
        pen.addComponent("missing", (1, 0, 0, 1, 0, 0))  # skipped
        compositeGlyph = pen.glyph()

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        pen.moveTo((2, 0))
        pen.lineTo((2, 1))
        pen.lineTo((3, 0))
        pen.closePath()
        plainGlyph = pen.glyph()

        assert plainGlyph == compositeGlyph

    def test_remove_extra_move_points(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.qCurveTo((100, 50), (50, 100), (0, 0))
        pen.closePath()
        assert len(pen.points) == 4
        assert pen.points[0] == (0, 0)

    def test_keep_move_point(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.qCurveTo((100, 50), (50, 100), (30, 30))
        # when last and move pts are different, closePath() implies a lineTo
        pen.closePath()
        assert len(pen.points) == 5
        assert pen.points[0] == (0, 0)

    def test_keep_duplicate_end_point(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.qCurveTo((100, 50), (50, 100), (0, 0))
        pen.lineTo((0, 0))  # the duplicate point is not removed
        pen.closePath()
        assert len(pen.points) == 5
        assert pen.points[0] == (0, 0)

    def test_within_range_component_transform(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (1.5, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, -1.5, 0, 0))
        compositeGlyph = pen.glyph()

        pen.addComponent(componentName, (1.5, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, -1.5, 0, 0))
        expectedGlyph = pen.glyph()

        assert expectedGlyph == compositeGlyph

    def test_clamp_to_almost_2_component_transform(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (1.99999, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 2, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 2, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (-2, 0, 0, -2, 0, 0))
        compositeGlyph = pen.glyph()

        almost2 = MAX_F2DOT14  # 0b1.11111111111111
        pen.addComponent(componentName, (almost2, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, almost2, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, almost2, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, almost2, 0, 0))
        pen.addComponent(componentName, (-2, 0, 0, -2, 0, 0))
        expectedGlyph = pen.glyph()

        assert expectedGlyph == compositeGlyph

    def test_out_of_range_transform_decomposed(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (3, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 1, -1, 2))
        pen.addComponent(componentName, (2, 0, 0, -3, 0, 0))
        compositeGlyph = pen.glyph()

        pen.moveTo((0, 0))
        pen.lineTo((0, 2))
        pen.lineTo((3, 0))
        pen.closePath()
        pen.moveTo((-1, 2))
        pen.lineTo((-1, 3))
        pen.lineTo((0, 2))
        pen.closePath()
        pen.moveTo((0, 0))
        pen.lineTo((0, -3))
        pen.lineTo((2, 0))
        pen.closePath()
        expectedGlyph = pen.glyph()

        assert expectedGlyph == compositeGlyph

    def test_no_handle_overflowing_transform(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPen(glyphSet, handleOverflowingTransforms=False)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        baseGlyph = pen.glyph()
        glyphSet[componentName] = _TestGlyph(baseGlyph)

        pen.addComponent(componentName, (3, 0, 0, 1, 0, 0))
        compositeGlyph = pen.glyph()

        assert compositeGlyph.components[0].transform == ((3, 0), (0, 1))

        with pytest.raises(struct.error):
            compositeGlyph.compile({"a": baseGlyph})

    def assertGlyphBoundsEqual(self, glyph, bounds):
        assert (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax) == bounds

    def test_round_float_coordinates_and_component_offsets(self):
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((367.6, 0))
        pen.closePath()
        simpleGlyph = pen.glyph()

        simpleGlyph.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(simpleGlyph, (0, 0, 368, 1))

        componentName = "a"
        glyphSet[componentName] = simpleGlyph

        pen.addComponent(componentName, (1, 0, 0, 1, -86.4, 0))
        compositeGlyph = pen.glyph()

        compositeGlyph.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(compositeGlyph, (-86, 0, 282, 1))

    def test_scaled_component_bounds(self):
        glyphSet = {}

        pen = TTGlyphPen(glyphSet)
        pen.moveTo((-231, 939))
        pen.lineTo((-55, 939))
        pen.lineTo((-55, 745))
        pen.lineTo((-231, 745))
        pen.closePath()
        glyphSet["gravecomb"] = pen.glyph()

        pen = TTGlyphPen(glyphSet)
        pen.moveTo((-278, 939))
        pen.lineTo((8, 939))
        pen.lineTo((8, 745))
        pen.lineTo((-278, 745))
        pen.closePath()
        glyphSet["circumflexcomb"] = pen.glyph()

        pen = TTGlyphPen(glyphSet)
        pen.addComponent("circumflexcomb", (1, 0, 0, 1, 0, 0))
        pen.addComponent("gravecomb", (0.9, 0, 0, 0.9, 198, 180))
        glyphSet["uni0302_uni0300"] = uni0302_uni0300 = pen.glyph()

        uni0302_uni0300.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(uni0302_uni0300, (-278, 745, 148, 1025))

    def test_outputImpliedClosingLine(self):
        glyphSet = {}

        pen = TTGlyphPen(glyphSet)
        pen.moveTo((0, 0))
        pen.lineTo((10, 0))
        pen.lineTo((0, 10))
        pen.lineTo((0, 0))
        pen.closePath()
        glyph = pen.glyph()
        assert len(glyph.coordinates) == 3

        pen = TTGlyphPen(glyphSet, outputImpliedClosingLine=True)
        pen.moveTo((0, 0))
        pen.lineTo((10, 0))
        pen.lineTo((0, 10))
        pen.lineTo((0, 0))
        pen.closePath()
        glyph = pen.glyph()
        assert len(glyph.coordinates) == 4


class TTGlyphPointPenTest(TTGlyphPenTestBase):
    penClass = TTGlyphPointPen
    drawMethod = "drawPoints"

    def test_glyph_simple(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((50, 0), "line")
        pen.addPoint((450, 0), "line")
        pen.addPoint((450, 700), "line")
        pen.addPoint((50, 700), "line")
        pen.endPath()
        glyph = pen.glyph()
        assert glyph.numberOfContours == 1
        assert glyph.endPtsOfContours == [3]

    def test_addPoint_noErrorOnCurve(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((0, 0), "curve")
        pen.endPath()

    def test_beginPath_beginPathOnOpenPath(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((0, 0))
        with pytest.raises(PenError):
            pen.beginPath()

    def test_glyph_errorOnUnendedContour(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((0, 0))
        with pytest.raises(PenError):
            pen.glyph()

    def test_glyph_decomposes(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        pen.addComponent(componentName, (1, 0, 0, 1, 2, 0))
        pen.addComponent("missing", (1, 0, 0, 1, 0, 0))  # skipped
        compositeGlyph = pen.glyph()

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        pen.beginPath()
        pen.addPoint((2, 0), "line")
        pen.addPoint((2, 1), "line")
        pen.addPoint((3, 0), "line")
        pen.endPath()
        plainGlyph = pen.glyph()

        assert plainGlyph == compositeGlyph

    def test_keep_duplicate_end_point(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((100, 0), "line")
        pen.addPoint((100, 50))
        pen.addPoint((50, 100))
        pen.addPoint((0, 0), "qcurve")
        pen.addPoint((0, 0), "line")  # the duplicate point is not removed
        pen.endPath()
        assert len(pen.points) == 6
        assert pen.points[0] == (0, 0)

    def test_within_range_component_transform(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (1.5, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, -1.5, 0, 0))
        compositeGlyph = pen.glyph()

        pen.addComponent(componentName, (1.5, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, -1.5, 0, 0))
        expectedGlyph = pen.glyph()

        assert expectedGlyph == compositeGlyph

    def test_clamp_to_almost_2_component_transform(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (1.99999, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 2, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 2, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (-2, 0, 0, -2, 0, 0))
        compositeGlyph = pen.glyph()

        almost2 = MAX_F2DOT14  # 0b1.11111111111111
        pen.addComponent(componentName, (almost2, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, almost2, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, almost2, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, almost2, 0, 0))
        pen.addComponent(componentName, (-2, 0, 0, -2, 0, 0))
        expectedGlyph = pen.glyph()

        assert expectedGlyph == compositeGlyph

    def test_out_of_range_transform_decomposed(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (3, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 1, -1, 2))
        pen.addComponent(componentName, (2, 0, 0, -3, 0, 0))
        compositeGlyph = pen.glyph()

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 2), "line")
        pen.addPoint((3, 0), "line")
        pen.endPath()
        pen.beginPath()
        pen.addPoint((-1, 2), "line")
        pen.addPoint((-1, 3), "line")
        pen.addPoint((0, 2), "line")
        pen.endPath()
        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, -3), "line")
        pen.addPoint((2, 0), "line")
        pen.endPath()
        expectedGlyph = pen.glyph()

        assert expectedGlyph == compositeGlyph

    def test_no_handle_overflowing_transform(self):
        componentName = "a"
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet, handleOverflowingTransforms=False)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        baseGlyph = pen.glyph()
        glyphSet[componentName] = _TestGlyph(baseGlyph)

        pen.addComponent(componentName, (3, 0, 0, 1, 0, 0))
        compositeGlyph = pen.glyph()

        assert compositeGlyph.components[0].transform == ((3, 0), (0, 1))

        with pytest.raises(struct.error):
            compositeGlyph.compile({"a": baseGlyph})

    def assertGlyphBoundsEqual(self, glyph, bounds):
        assert (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax) == bounds

    def test_round_float_coordinates_and_component_offsets(self):
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((367.6, 0), "line")
        pen.endPath()
        simpleGlyph = pen.glyph()

        simpleGlyph.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(simpleGlyph, (0, 0, 368, 1))

        componentName = "a"
        glyphSet[componentName] = simpleGlyph

        pen.addComponent(componentName, (1, 0, 0, 1, -86.4, 0))
        compositeGlyph = pen.glyph()

        compositeGlyph.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(compositeGlyph, (-86, 0, 282, 1))

    def test_scaled_component_bounds(self):
        glyphSet = {}

        pen = TTGlyphPointPen(glyphSet)
        pen.beginPath()
        pen.addPoint((-231, 939), "line")
        pen.addPoint((-55, 939), "line")
        pen.addPoint((-55, 745), "line")
        pen.addPoint((-231, 745), "line")
        pen.endPath()
        glyphSet["gravecomb"] = pen.glyph()

        pen = TTGlyphPointPen(glyphSet)
        pen.beginPath()
        pen.addPoint((-278, 939), "line")
        pen.addPoint((8, 939), "line")
        pen.addPoint((8, 745), "line")
        pen.addPoint((-278, 745), "line")
        pen.endPath()
        glyphSet["circumflexcomb"] = pen.glyph()

        pen = TTGlyphPointPen(glyphSet)
        pen.addComponent("circumflexcomb", (1, 0, 0, 1, 0, 0))
        pen.addComponent("gravecomb", (0.9, 0, 0, 0.9, 198, 180))
        glyphSet["uni0302_uni0300"] = uni0302_uni0300 = pen.glyph()

        uni0302_uni0300.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(uni0302_uni0300, (-278, 745, 148, 1025))

    def test_open_path_starting_with_move(self):
        # when a contour starts with a 'move' point, it signifies the beginnig
        # of an open contour.
        # https://unifiedfontobject.org/versions/ufo3/glyphs/glif/#point-types
        pen1 = TTGlyphPointPen(None)
        pen1.beginPath()
        pen1.addPoint((0, 0), "move")  # contour is open
        pen1.addPoint((10, 10), "line")
        pen1.addPoint((20, 20))
        pen1.addPoint((20, 0), "qcurve")
        pen1.endPath()

        pen2 = TTGlyphPointPen(None)
        pen2.beginPath()
        pen2.addPoint((0, 0), "line")  # contour is closed
        pen2.addPoint((10, 10), "line")
        pen2.addPoint((20, 20))
        pen2.addPoint((20, 0), "qcurve")
        pen2.endPath()

        # Since TrueType contours are always implicitly closed, the pen will
        # interpret both these paths as equivalent
        assert pen1.points == pen2.points == [(0, 0), (10, 10), (20, 20), (20, 0)]
        assert pen1.types == pen2.types == [1, 1, 0, 1]

    def test_skip_empty_contours(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.endPath()
        pen.beginPath()
        pen.endPath()
        glyph = pen.glyph()
        assert glyph.numberOfContours == 0


class CubicGlyfTest:
    def test_cubic_simple(self):
        spen = TTGlyphPen(None)
        spen.moveTo((0, 0))
        spen.curveTo((0, 1), (1, 1), (1, 0))
        spen.closePath()

        ppen = TTGlyphPointPen(None)
        ppen.beginPath()
        ppen.addPoint((0, 0), "line")
        ppen.addPoint((0, 1))
        ppen.addPoint((1, 1))
        ppen.addPoint((1, 0), "curve")
        ppen.endPath()

        for pen in (spen, ppen):
            glyph = pen.glyph()

            for i in range(2):
                if i == 1:
                    glyph.compile(None)

                assert list(glyph.coordinates) == [(0, 0), (0, 1), (1, 1), (1, 0)]
                assert list(glyph.flags) == [0x01, 0x80, 0x80, 0x01]

                rpen = RecordingPen()
                glyph.draw(rpen, None)
                assert rpen.value == [
                    ("moveTo", ((0, 0),)),
                    (
                        "curveTo",
                        (
                            (0, 1),
                            (1, 1),
                            (1, 0),
                        ),
                    ),
                    ("closePath", ()),
                ]

    @pytest.mark.parametrize(
        "dropImpliedOnCurves, segment_pen_commands, point_pen_commands, expected_coordinates, expected_flags, expected_endPts",
        [
            (  # Two curves that do NOT merge; request merging
                True,
                [
                    ("moveTo", ((0, 0),)),
                    ("curveTo", ((0, 1), (1, 2), (2, 2))),
                    ("curveTo", ((3, 3), (4, 1), (4, 0))),
                    ("closePath", ()),
                ],
                [
                    ("beginPath", (), {}),
                    ("addPoint", ((0, 0), "line", None, None), {}),
                    ("addPoint", ((0, 1), None, None, None), {}),
                    ("addPoint", ((1, 2), None, None, None), {}),
                    ("addPoint", ((2, 2), "curve", None, None), {}),
                    ("addPoint", ((3, 3), None, None, None), {}),
                    ("addPoint", ((4, 1), None, None, None), {}),
                    ("addPoint", ((4, 0), "curve", None, None), {}),
                    ("endPath", (), {}),
                ],
                [(0, 0), (0, 1), (1, 2), (2, 2), (3, 3), (4, 1), (4, 0)],
                [0x01, 0x80, 0x80, 0x01, 0x80, 0x80, 0x01],
                [6],
            ),
            (  # Two curves that merge; request merging
                True,
                [
                    ("moveTo", ((0, 0),)),
                    ("curveTo", ((0, 1), (1, 2), (2, 2))),
                    ("curveTo", ((3, 2), (4, 1), (4, 0))),
                    ("closePath", ()),
                ],
                [
                    ("beginPath", (), {}),
                    ("addPoint", ((0, 0), "line", None, None), {}),
                    ("addPoint", ((0, 1), None, None, None), {}),
                    ("addPoint", ((1, 2), None, None, None), {}),
                    ("addPoint", ((2, 2), "curve", None, None), {}),
                    ("addPoint", ((3, 2), None, None, None), {}),
                    ("addPoint", ((4, 1), None, None, None), {}),
                    ("addPoint", ((4, 0), "curve", None, None), {}),
                    ("endPath", (), {}),
                ],
                [(0, 0), (0, 1), (1, 2), (3, 2), (4, 1), (4, 0)],
                [0x01, 0x80, 0x80, 0x80, 0x80, 0x01],
                [5],
            ),
            (  # Two curves that merge; request NOT merging
                False,
                [
                    ("moveTo", ((0, 0),)),
                    ("curveTo", ((0, 1), (1, 2), (2, 2))),
                    ("curveTo", ((3, 2), (4, 1), (4, 0))),
                    ("closePath", ()),
                ],
                [
                    ("beginPath", (), {}),
                    ("addPoint", ((0, 0), "line", None, None), {}),
                    ("addPoint", ((0, 1), None, None, None), {}),
                    ("addPoint", ((1, 2), None, None, None), {}),
                    ("addPoint", ((2, 2), "curve", None, None), {}),
                    ("addPoint", ((3, 2), None, None, None), {}),
                    ("addPoint", ((4, 1), None, None, None), {}),
                    ("addPoint", ((4, 0), "curve", None, None), {}),
                    ("endPath", (), {}),
                ],
                [(0, 0), (0, 1), (1, 2), (2, 2), (3, 2), (4, 1), (4, 0)],
                [0x01, 0x80, 0x80, 0x01, 0x80, 0x80, 0x01],
                [6],
            ),
            (  # Two (duplicate) contours
                True,
                [
                    ("moveTo", ((0, 0),)),
                    ("curveTo", ((0, 1), (1, 2), (2, 2))),
                    ("curveTo", ((3, 2), (4, 1), (4, 0))),
                    ("closePath", ()),
                    ("moveTo", ((0, 0),)),
                    ("curveTo", ((0, 1), (1, 2), (2, 2))),
                    ("curveTo", ((3, 2), (4, 1), (4, 0))),
                    ("closePath", ()),
                ],
                [
                    ("beginPath", (), {}),
                    ("addPoint", ((0, 0), "line", None, None), {}),
                    ("addPoint", ((0, 1), None, None, None), {}),
                    ("addPoint", ((1, 2), None, None, None), {}),
                    ("addPoint", ((2, 2), "curve", None, None), {}),
                    ("addPoint", ((3, 2), None, None, None), {}),
                    ("addPoint", ((4, 1), None, None, None), {}),
                    ("addPoint", ((4, 0), "curve", None, None), {}),
                    ("endPath", (), {}),
                    ("beginPath", (), {}),
                    ("addPoint", ((0, 0), "line", None, None), {}),
                    ("addPoint", ((0, 1), None, None, None), {}),
                    ("addPoint", ((1, 2), None, None, None), {}),
                    ("addPoint", ((2, 2), "curve", None, None), {}),
                    ("addPoint", ((3, 2), None, None, None), {}),
                    ("addPoint", ((4, 1), None, None, None), {}),
                    ("addPoint", ((4, 0), "curve", None, None), {}),
                    ("endPath", (), {}),
                ],
                [
                    (0, 0),
                    (0, 1),
                    (1, 2),
                    (3, 2),
                    (4, 1),
                    (4, 0),
                    (0, 0),
                    (0, 1),
                    (1, 2),
                    (3, 2),
                    (4, 1),
                    (4, 0),
                ],
                [
                    0x01,
                    0x80,
                    0x80,
                    0x80,
                    0x80,
                    0x01,
                    0x01,
                    0x80,
                    0x80,
                    0x80,
                    0x80,
                    0x01,
                ],
                [5, 11],
            ),
        ],
    )
    def test_cubic_topology(
        self,
        dropImpliedOnCurves,
        segment_pen_commands,
        point_pen_commands,
        expected_coordinates,
        expected_flags,
        expected_endPts,
    ):
        spen = TTGlyphPen(None)
        rpen = RecordingPen()
        rpen.value = segment_pen_commands
        rpen.replay(spen)

        ppen = TTGlyphPointPen(None)
        rpen = RecordingPointPen()
        rpen.value = point_pen_commands
        rpen.replay(ppen)

        for pen in (spen, ppen):
            glyph = pen.glyph(dropImpliedOnCurves=dropImpliedOnCurves)

            assert list(glyph.coordinates) == expected_coordinates
            assert list(glyph.flags) == expected_flags
            assert list(glyph.endPtsOfContours) == expected_endPts

            rpen = RecordingPen()
            glyph.draw(rpen, None)
            assert rpen.value == segment_pen_commands


class _TestGlyph(object):
    def __init__(self, glyph):
        self.coordinates = glyph.coordinates

    def draw(self, pen):
        pen.moveTo(self.coordinates[0])
        for point in self.coordinates[1:]:
            pen.lineTo(point)
        pen.closePath()

    def drawPoints(self, pen):
        pen.beginPath()
        for point in self.coordinates:
            pen.addPoint(point, "line")
        pen.endPath()
