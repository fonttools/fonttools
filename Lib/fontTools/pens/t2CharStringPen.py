# Copyright (c) 2009 Type Supply LLC
# Author: Tal Leming

from __future__ import annotations

from typing import Any

from fontTools.cffLib.specializer import commandsToProgram, specializeCommands
from fontTools.misc.psCharStrings import T2CharString
from fontTools.misc.roundTools import otRound, roundFunc
from fontTools.pens.basePen import BasePen, PenError
from fontTools.pens.pointPen import PointToSegmentPen
from typing_extensions import NotRequired, TypedDict


class UfoHintSet(TypedDict):
    pointTag: str
    stems: list[str]


class UfoHintingV2(TypedDict):
    flexList: NotRequired[list[str]]
    hintSetList: NotRequired[list[UfoHintSet]]
    id: NotRequired[str]


class T2CharStringPen(BasePen):
    """Pen to draw Type 2 CharStrings.

    The 'roundTolerance' argument controls the rounding of point coordinates.
    It is defined as the maximum absolute difference between the original
    float and the rounded integer value.
    The default tolerance of 0.5 means that all floats are rounded to integer;
    a value of 0 disables rounding; values in between will only round floats
    which are close to their integral part within the tolerated range.
    """

    def __init__(
        self,
        width: float,
        glyphSet: dict[str, Any] | None,
        roundTolerance: float = 0.5,
        CFF2: bool = False,
    ) -> None:
        super(T2CharStringPen, self).__init__(glyphSet)
        self.round = roundFunc(roundTolerance)
        self._CFF2 = CFF2
        self._width = width
        self._commands: list[tuple[str, list[float]]] = []
        self._p0 = (0, 0)

    def _p(self, pt: tuple[float, float]) -> list[float]:
        p0 = self._p0
        pt = self._p0 = (self.round(pt[0]), self.round(pt[1]))
        return [pt[0] - p0[0], pt[1] - p0[1]]

    def _moveTo(self, pt: tuple[float, float]) -> None:
        self._commands.append(("rmoveto", self._p(pt)))

    def _lineTo(self, pt: tuple[float, float]) -> None:
        self._commands.append(("rlineto", self._p(pt)))

    def _curveToOne(
        self,
        pt1: tuple[float, float],
        pt2: tuple[float, float],
        pt3: tuple[float, float],
    ) -> None:
        _p = self._p
        self._commands.append(("rrcurveto", _p(pt1) + _p(pt2) + _p(pt3)))

    def _closePath(self) -> None:
        pass

    def _endPath(self) -> None:
        pass

    def getCharString(
        self,
        private: dict | None = None,
        globalSubrs: list | None = None,
        optimize: bool = True,
    ) -> T2CharString:
        commands = self._commands
        if optimize:
            maxstack = 48 if not self._CFF2 else 513
            commands = specializeCommands(
                commands, generalizeFirst=False, maxstack=maxstack
            )
        program = commandsToProgram(commands)
        if self._width is not None:
            assert (
                not self._CFF2
            ), "CFF2 does not allow encoding glyph width in CharString."
            program.insert(0, otRound(self._width))
        if not self._CFF2:
            program.append("endchar")
        charString = T2CharString(
            program=program, private=private, globalSubrs=globalSubrs
        )
        return charString


class T2CharStringPointPen(PointToSegmentPen):
    def __init__(
        self,
        width: float,
        glyphSet: dict[str, Any] | None,
        roundTolerance: float = 0.5,
        CFF2: bool = False,
        hints: UfoHintingV2 | None = None,
    ) -> None:
        super(T2CharStringPointPen, self).__init__(T2CharStringPen(width, glyphSet))
        self.round = roundFunc(roundTolerance)
        self._CFF2 = CFF2
        self._width = width
        self._commands: list[tuple[str, list[float]]] = []
        self._p0 = (0, 0)
        # The _hints property contains a dict that matches the structure of the hinting
        # lib entry from UFO
        self._hints: UfoHintingV2 = hints if hints is not None else {}
        self._addStemHints()

    def _addStemHints(self) -> None:
        # Collect all stem hints and put the corresponding commands at the beginning of
        # the charstring
        stems: dict[str, set[tuple[float, float]]] = {"hstem": set(), "vstem": set()}
        self._hintSetList = self._hints.get("hintSetList", [])
        self._hintMasksUsed = len(self._hintSetList) > 1
        for hintSet in self._hintSetList:
            for stem in hintSet.get("stems", []):
                cmd, pos, size = stem.split()
                stems[cmd].add((self.round(float(pos)), self.round(float(size))))

        self._seenHstemHM = False
        p0: float = 0
        for direction in ("hstem", "vstem"):
            p0 = 0
            stem_values = []
            for p, s in sorted(stems[direction]):
                stem_values.extend([p - p0, s])
                p0 += self.round(p + s)
            if self._hintMasksUsed:
                # (h|v)stemhm has the same meaning as (h|v)stem except that it must be
                # used in place of (h|v)stem if the charstring contains one or more
                # hintmask operators.
                direction += "hm"
                if direction == "hstemhm":
                    self._seenHstemHM = True
            self.pen._commands.append((direction, stem_values))

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ) -> None:
        if self.currentPath is None:
            raise PenError("Path not begun")

        if name is not None and self._hintMasksUsed:
            # Build the hint mask

            # FIXME: By adding the hintmask commands manually, they are inserted before
            # the contour is flushed, so they end up at the beginning of the program,
            # not in the correct place connected to the point.
            for hintSet in self._hintSetList:
                args = []
                if name == hintSet["pointTag"]:
                    # Optimization: If hstem and vstem hints are both declared at the
                    # beginning of a charstring, and this sequence is followed directly
                    # by the hintmask or cntrmask operators, the vstem hint operator
                    # need not be included.
                    if self._seenHstemHM and self.pen._commands[-1][0] == "vstemhm":
                        _, args = self.pen._commands.pop()
                    self.pen._commands.append(("hintmask", args))
                    # FIXME: Compute the actual hintmask
                    self.pen._commands.append((b"\xd8", []))
                    break

        self.currentPath.append((pt, segmentType, smooth, name, kwargs))

    def getCharString(
        self,
        private: dict | None = None,
        globalSubrs: list | None = None,
        optimize: bool = True,
    ) -> T2CharString:
        return self.pen.getCharString(private, globalSubrs, optimize)
