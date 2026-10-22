"""CFF2 instancing rounds absolute positions, so contours stay closed."""

from fontTools.cffLib.specializer import (
    commandsToProgram,
    generalizeCommands,
    programToCommands,
)
from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    SourceDescriptor,
)
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import noRound
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from fontTools import varLib
from fontTools.varLib import builder, instancer
from copy import deepcopy
from io import BytesIO
import logging
import math
import pytest

GLYPH_ORDER = [".notdef", "o"]


def drawRing(pen, radius, wobble):
    # A closed contour of 16 curves, the last of which ends on the first point.
    steps = 16
    points = [
        (
            round(
                400 + (radius + wobble * (i % 3)) * math.cos(2 * math.pi * i / steps)
            ),
            round(
                400 + (radius - wobble * (i % 2)) * math.sin(2 * math.pi * i / steps)
            ),
        )
        for i in range(steps)
    ]
    pen.moveTo(points[0])
    for i in range(steps):
        (x0, y0), (x1, y1) = points[i], points[(i + 1) % steps]
        pen.curveTo(
            (x0 + (x1 - x0) // 3, y0 + (y1 - y0) // 3),
            (x1 - (x1 - x0) // 3, y1 - (y1 - y0) // 3),
            (x1, y1),
        )
    pen.closePath()


def makeMaster(radius, wobble, hinted):
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(GLYPH_ORDER)
    fb.setupCharacterMap({ord("o"): "o"})
    charStrings = {}
    for glyphName in GLYPH_ORDER:
        pen = T2CharStringPen(800, None)
        drawRing(pen, radius, wobble)
        charString = pen.getCharString()
        width, *program = charString.program
        if hinted:
            # Stem over the ring's full height, with a hintmask
            stem = [400 - radius, 2 * radius, "hstemhm"]
            program = stem + ["hintmask", b"\x80"] + program
        charString.program = [width] + program
        charStrings[glyphName] = charString
    fb.setupCFF("Ring-Regular", {"FullName": "Ring"}, charStrings, {})
    fb.setupHorizontalMetrics({glyphName: (800, 0) for glyphName in GLYPH_ORDER})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Ring", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    return fb.font


def reload(font):
    buf = BytesIO()
    font.save(buf)
    buf.seek(0)
    return TTFont(buf)


def makeRingVF(masters, hinted=False, flex=False):
    # CFF2 VF over wght 300-900 (default 300) and slnt -11-0;
    # masters {(wght, slnt): (radius, wobble)}
    doc = DesignSpaceDocument()
    for tag, name, (minimum, default, maximum) in (
        ("wght", "Weight", (300, 300, 900)),
        ("slnt", "Slant", (-11, 0, 0)),
    ):
        axis = AxisDescriptor()
        axis.tag, axis.name = tag, name
        axis.minimum, axis.default, axis.maximum = minimum, default, maximum
        doc.addAxis(axis)
    for (weight, slant), (radius, wobble) in masters.items():
        source = SourceDescriptor()
        source.font = makeMaster(radius, wobble, hinted)
        source.location = {"Weight": weight, "Slant": slant}
        source.name = f"master-{weight}-{slant}"
        doc.addSource(source)
    vf, _, _ = varLib.build(doc)
    if flex:
        # varLib's merge drops flex; turn the first two curves into one
        charString = vf["CFF2"].cff.topDictIndex[0].CharStrings["o"]
        charString.decompile()
        commands = generalizeCommands(
            programToCommands(
                charString.program, getNumRegions=charString.private.getNumRegions
            )
        )
        first = [op for op, _ in commands].index("rrcurveto")
        assert [op for op, _ in commands[first : first + 2]] == ["rrcurveto"] * 2
        flexArgs = commands[first][1] + commands[first + 1][1] + [50]
        commands[first : first + 2] = [("flex", flexArgs)]
        charString.program = commandsToProgram(commands)
    return reload(vf)


def makeVF(commands):
    # The ring font with the given commands as "o" (one wght region)
    vf = makeRingVF(TWO_MASTERS)
    charString = vf["CFF2"].cff.topDictIndex[0].CharStrings["o"]
    charString.decompile()
    charString.program = commandsToProgram(commands)
    return reload(vf)


# Two masters on wght; rebasing the default to 400 lands between them.
TWO_MASTERS = {(300, 0): (300, 7), (900, 0): (337, 23)}
# Corners on both axes plus an intermediate weight, so that regions overlap.
SIX_MASTERS = {
    (300, 0): (300, 7),
    (900, 0): (337, 23),
    (300, -11): (305, 11),
    (900, -11): (343, 29),
    (600, 0): (321, 13),
    (600, -11): (326, 17),
}
# Masters off the axis ends on both axes: varLib leaves fractional deltas.
OFF_END_MASTERS = {
    (300, 0): (300, 7),
    (350, 0): (303, 8),
    (900, 0): (337, 23),
    (300, -11): (305, 11),
    (380, -11): (311, 19),
    (900, -11): (343, 29),
}


def getContours(font, location):
    pen = RecordingPen()
    font.getGlyphSet(location=location)["o"].draw(pen)
    contours = []
    for op, args in pen.value:
        if op == "moveTo":
            contours.append([args[0]])
        elif op != "closePath":
            contours[-1].extend(args)
    return contours


# Float noise of drawing at a location.
EPSILON = 0.01


def assertClosed(font, location):
    for contour in getContours(font, location):
        (sx, sy), (ex, ey) = contour[0], contour[-1]
        assert (sx, sy) == pytest.approx((ex, ey), abs=1e-6), location


def assertCloseTo(font, location, reference, referenceLocation, tolerance):
    got = getContours(font, location)
    expected = getContours(reference, referenceLocation)
    assert [len(c) for c in got] == [len(c) for c in expected]
    for gotContour, expectedContour in zip(got, expected):
        for (gx, gy), (ex, ey) in zip(gotContour, expectedContour):
            assert abs(gx - ex) <= tolerance + EPSILON, location
            assert abs(gy - ey) <= tolerance + EPSILON, location


def getProgram(font):
    charString = font["CFF2"].cff.topDictIndex[0].CharStrings["o"]
    charString.decompile()
    return charString.program


class InstantiateCFF2RoundingTest:
    def test_rebased_default_contours_stay_closed(self):
        vf = makeRingVF(TWO_MASTERS)

        rebased = reload(
            instancer.instantiateVariableFont(vf, {"wght": (300, 400, 900)})
        )

        assertClosed(rebased, {})
        assertCloseTo(rebased, {}, vf, {"wght": 400}, 0.5)
        for weight in range(300, 901, 50):
            assertClosed(rebased, {"wght": weight})
            assertCloseTo(rebased, {"wght": weight}, vf, {"wght": weight}, 0.5)

    def test_static_instance_contours_stay_closed(self):
        # https://github.com/fonttools/fonttools/issues/3649
        vf = makeRingVF(SIX_MASTERS)

        for weight in (350, 400, 450, 500, 750):
            for slant in (0, -5.5):
                location = {"wght": weight, "slnt": slant}
                instance = reload(instancer.instantiateVariableFont(vf, location))

                assert "CFF2" in instance
                assert not hasattr(instance["CFF2"].cff.topDictIndex[0], "VarStore")
                assertClosed(instance, {})
                assertCloseTo(instance, {}, vf, location, 0.5)

    def test_overlapping_regions(self):
        vf = makeRingVF(SIX_MASTERS)

        rebased = reload(
            instancer.instantiateVariableFont(vf, {"wght": (300, 400, 900)})
        )

        assertCloseTo(rebased, {}, vf, {"wght": 400}, 0.5)
        for weight in (300, 400, 450, 600, 750, 900):
            for slant in (0, -5.5, -11):
                location = {"wght": weight, "slnt": slant}
                assertClosed(rebased, location)
                # Regions round separately, as in gvar
                assertCloseTo(rebased, location, vf, location, 1)

    def test_pinned_axis_and_rebased_default(self):
        vf = makeRingVF(SIX_MASTERS)

        italic = instancer.instantiateVariableFont(
            vf, {"slnt": -11, "wght": (300, 400, 900)}
        )
        italic = reload(italic)

        assert [axis.axisTag for axis in italic["fvar"].axes] == ["wght"]
        for weight in (300, 400, 600, 900):
            assertClosed(italic, {"wght": weight})
            assertCloseTo(
                italic, {"wght": weight}, vf, {"wght": weight, "slnt": -11}, 0.5
            )

    def test_fractional_deltas(self):
        # Off-end masters leave fractional deltas
        vf = makeRingVF(OFF_END_MASTERS)

        italic = instancer.instantiateVariableFont(
            vf, {"slnt": -11, "wght": (300, 400, 900)}
        )
        italic = reload(italic)

        for weight in range(300, 901, 2):
            assertClosed(italic, {"wght": weight})
            assertCloseTo(
                italic, {"wght": weight}, vf, {"wght": weight, "slnt": -11}, 1
            )

    def test_no_round(self):
        vf = makeRingVF(SIX_MASTERS)
        reference = reload(vf)
        limits = instancer.NormalizedAxisLimits({"wght": (0, 0.5, 1), "slnt": -1})

        instancer.instantiateCFF2(vf, limits, round=noRound)

        # wght 600 is the new default, slnt -11 is pinned; nothing is rounded.
        assertCloseTo(vf, {}, reference, {"wght": 600, "slnt": -11}, 0)

    def test_private_dict_vsindex(self):
        # Blends use VarData 1 via the Private DICT; VarData 0 differs
        vf = makeRingVF(TWO_MASTERS)
        topDict = vf["CFF2"].cff.topDictIndex[0]
        varStore = topDict.VarStore.otVarStore
        varStore.VarData.insert(0, builder.buildVarData([], []))
        varStore.VarDataCount = len(varStore.VarData)
        topDict.FDArray[0].Private.vsindex = 1
        vf = reload(vf)

        rebased = reload(
            instancer.instantiateVariableFont(vf, {"wght": (300, 400, 900)})
        )

        assertClosed(rebased, {})
        assertCloseTo(rebased, {}, vf, {"wght": 400}, 0.5)
        assertCloseTo(rebased, {"wght": 900}, vf, {"wght": 900}, 0.5)

    def test_hinted_charstrings_keep_their_hints(self):
        vf = makeRingVF(TWO_MASTERS, hinted=True)

        rebased = reload(
            instancer.instantiateVariableFont(vf, {"wght": (300, 400, 900)})
        )

        program = getProgram(rebased)
        assert "hstemhm" in program
        assert program[program.index("hintmask") + 1] == b"\x80"
        assertClosed(rebased, {})
        assertCloseTo(rebased, {}, vf, {"wght": 400}, 0.5)

    def test_stem_edges_stay_on_the_outline(self):
        # At wght 570 a relative stem would end a unit off the ring's top
        vf = makeRingVF(TWO_MASTERS, hinted=True)

        instance = reload(instancer.instantiateVariableFont(vf, {"wght": 570}))

        program = getProgram(instance)
        assert program[2] == "hstemhm"
        bottom, height = program[:2]
        ys = [y for contour in getContours(instance, {}) for _, y in contour]
        assert (bottom, bottom + height) == (min(ys), max(ys))

    def test_ghost_hint(self):
        # Ghost hint edges at .5 after rebasing; the width must stay -21
        vf = makeVF(
            [
                ("hstemhm", [[101, 3, 1], -21]),
                ("hintmask", []),
                ("", [b"\x80"]),
                ("rmoveto", [[100, 3, 1], 100]),
                ("rlineto", [51, 0, 0, 50]),
            ]
        )

        rebased = reload(
            instancer.instantiateVariableFont(vf, {"wght": (300, 600, 900)})
        )

        program = getProgram(rebased)
        assert program[: program.index("hstemhm") + 1][-2:] == [-21, "hstemhm"]

    def test_rounding_keeps_distances(self):
        # Edges 51 apart at .5: half-to-even would give 50 or 52
        vf = makeVF([("rmoveto", [[100, 3, 1], 100]), ("rlineto", [51, 0, 0, 50])])

        rebased = instancer.instantiateVariableFont(vf, {"wght": (300, 600, 900)})

        (x0, _), (x1, _), _ = getContours(reload(rebased), {})[0]
        assert (x0, x1) == (102, 153)

    def test_fractional_outline(self):
        vf = makeVF(
            [("rmoveto", [[100.25, 3, 1], 100.5]), ("rlineto", [51, 0, 0, 50.5])]
        )
        limits = instancer.NormalizedAxisLimits({"wght": (0, 0.5, 1), "slnt": 0})
        unrounded = deepcopy(vf)

        # Points that did not move are rounded along with those that did.
        instancer.instantiateCFF2(vf, limits)
        points = getContours(vf, {})[0]
        assert points[:2] == [(102, 101), (153, 101)]

        instancer.instantiateCFF2(unrounded, limits, round=noRound)
        points = getContours(unrounded, {})[0]
        assert points[:2] == [(101.75, 100.5), (152.75, 100.5)]

    def test_flex(self):
        vf = makeRingVF(TWO_MASTERS, flex=True)
        assert "flex" in getProgram(vf)

        rebased = reload(
            instancer.instantiateVariableFont(vf, {"wght": (300, 400, 900)})
        )

        assert "flex" in getProgram(rebased)
        assertClosed(rebased, {})
        assertCloseTo(rebased, {}, vf, {"wght": 400}, 0.5)
        for weight in (300, 600, 900):
            assertClosed(rebased, {"wght": weight})

    # flex1 ends horizontally at wght 300, vertically at 900
    FLEX1_CHANGING_DIRECTION = [
        10, 10, 10, [-10, 20, 1], 10, 0, 10, 0, 10, [0, 40, 1], 0
    ]  # fmt: skip

    def test_flex1_changing_direction(self, caplog):
        # Direction varies across the remaining wght range: fallback
        flex1 = self.FLEX1_CHANGING_DIRECTION
        vf = makeVF([("rmoveto", [100, 100]), ("flex1", flex1), ("rlineto", [-50, 0])])

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            instance = instancer.instantiateVariableFont(vf, {"wght": (300, 300, 900)})
        instance = reload(instance)

        assert "'o': flex1 changes direction" in caplog.text
        assert "flex1" in getProgram(instance)
        assertCloseTo(instance, {}, vf, {}, 0)
        assertCloseTo(instance, {"wght": 900}, vf, {"wght": 900}, 0)

    def test_flex1_direction_at_pinned_location(self, caplog):
        # Pinned, the direction is known
        flex1 = self.FLEX1_CHANGING_DIRECTION
        vf = makeVF([("rmoveto", [100, 100]), ("flex1", flex1), ("rlineto", [-50, 0])])

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            instance = instancer.instantiateVariableFont(vf, {"wght": 900})
        instance = reload(instance)

        assert "flex1 changes direction" not in caplog.text
        assertCloseTo(instance, {}, vf, {"wght": 900}, 0)

    def test_flex1_direction_with_invalid_tent(self, caplog):
        # Invalid tent: direction unknown, fallback
        flex1 = self.FLEX1_CHANGING_DIRECTION
        vf = makeVF([("rmoveto", [100, 100]), ("flex1", flex1), ("rlineto", [-50, 0])])
        varStore = vf["CFF2"].cff.topDictIndex[0].VarStore.otVarStore
        varStore.VarRegionList.Region[0].VarRegionAxis[0].EndCoord = 0.5
        vf = reload(vf)

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            instance = instancer.instantiateVariableFont(vf, {"wght": 900})
        instance = reload(instance)

        assert "'o': flex1 changes direction" in caplog.text
        assert "flex1" in getProgram(instance)

    def test_vsindex_after_blend(self, caplog):
        # vsindex after a blend is invalid CFF2: fallback, not an error
        vf = makeVF(
            [
                ("rmoveto", [100, [100, 50, 1]]),
                ("vsindex", [0]),
                ("rlineto", [[50, 10, 1], 0, 0, 50, -50, 0]),
            ]
        )

        with caplog.at_level(logging.WARNING, logger="fontTools.varLib.instancer"):
            rebased = instancer.instantiateVariableFont(vf, {"wght": (300, 400, 900)})
        rebased = reload(rebased)

        assert "'o': vsindex after a blend" in caplog.text
        assertCloseTo(rebased, {}, vf, {"wght": 400}, 1)

    def test_fractional_private_dict_values(self):
        vf = makeRingVF(TWO_MASTERS)
        private = vf["CFF2"].cff.topDictIndex[0].FDArray[0].Private
        private.BlueScale = [0.039625, 0.02]
        vf = reload(vf)

        rebased = instancer.instantiateVariableFont(vf, {"wght": (300, 600, 900)})

        private = rebased["CFF2"].cff.topDictIndex[0].FDArray[0].Private
        # Both the default and its folded delta retain their fractional parts.
        assert private.BlueScale[0] == pytest.approx(0.049625)

    def test_private_dict_vsindex_and_charstring_vsindex(self):
        # Private DICT VarData 1 is emptied; the charstring's VarData 0 stays
        vf = makeRingVF(TWO_MASTERS)
        topDict = vf["CFF2"].cff.topDictIndex[0]
        varStore = topDict.VarStore.otVarStore
        region = builder.buildVarRegion({"slnt": (-1, -1, 0)}, ["wght", "slnt"])
        varStore.VarRegionList.Region.append(region)
        varStore.VarRegionList.RegionCount += 1
        varStore.VarData.append(
            builder.buildVarData([len(varStore.VarRegionList.Region) - 1], [])
        )
        varStore.VarDataCount = len(varStore.VarData)
        topDict.FDArray[0].Private.vsindex = 1
        for charString in topDict.CharStrings.values():
            charString.decompile()
            charString.program = [0, "vsindex"] + charString.program
        vf = reload(vf)

        rebased = instancer.instantiateVariableFont(
            vf, {"wght": (300, 400, 900), "slnt": 0}
        )
        rebased = reload(rebased)

        assertClosed(rebased, {})
        assertCloseTo(rebased, {}, vf, {"wght": 400}, 0.5)
