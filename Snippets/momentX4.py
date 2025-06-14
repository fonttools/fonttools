from fontTools.pens.basePen import BasePen, OpenContourError

try:
    import cython
except (AttributeError, ImportError):
    # if cython not installed, use mock module with no-op decorators and types
    from fontTools.misc import cython
COMPILED = cython.compiled


__all__ = ["MomentX4Pen"]


class MomentX4Pen(BasePen):

    def __init__(self, glyphset=None):
        BasePen.__init__(self, glyphset)

        self.momentX4 = 0

    def _moveTo(self, p0):
        self._startPoint = p0

    def _closePath(self):
        p0 = self._getCurrentPoint()
        if p0 != self._startPoint:
            self._lineTo(self._startPoint)

    def _endPath(self):
        p0 = self._getCurrentPoint()
        if p0 != self._startPoint:
            raise OpenContourError("Glyph statistics is not defined on open contours.")

    @cython.locals(r0=cython.double)
    @cython.locals(r1=cython.double)
    @cython.locals(x0=cython.double, y0=cython.double)
    @cython.locals(x1=cython.double, y1=cython.double)
    def _lineTo(self, p1):
        x0, y0 = self._getCurrentPoint()
        x1, y1 = p1

        r0 = x1**5
        r1 = y0 - y1

        self.momentX4 += (
            -r0 * y0 / 30
            - r0 * y1 / 6
            - r1 * x0**4 * x1 / 30
            - r1 * x0**3 * x1**2 / 30
            - r1 * x0**2 * x1**3 / 30
            - r1 * x0 * x1**4 / 30
            + x0**5 * (5 * y0 + y1) / 30
        )

    @cython.locals(r0=cython.double)
    @cython.locals(r1=cython.double)
    @cython.locals(r2=cython.double)
    @cython.locals(r3=cython.double)
    @cython.locals(r4=cython.double)
    @cython.locals(r5=cython.double)
    @cython.locals(r6=cython.double)
    @cython.locals(r7=cython.double)
    @cython.locals(r8=cython.double)
    @cython.locals(r9=cython.double)
    @cython.locals(r10=cython.double)
    @cython.locals(r11=cython.double)
    @cython.locals(r12=cython.double)
    @cython.locals(r13=cython.double)
    @cython.locals(r14=cython.double)
    @cython.locals(r15=cython.double)
    @cython.locals(r16=cython.double)
    @cython.locals(r17=cython.double)
    @cython.locals(r18=cython.double)
    @cython.locals(r19=cython.double)
    @cython.locals(r20=cython.double)
    @cython.locals(r21=cython.double)
    @cython.locals(r22=cython.double)
    @cython.locals(r23=cython.double)
    @cython.locals(r24=cython.double)
    @cython.locals(r25=cython.double)
    @cython.locals(r26=cython.double)
    @cython.locals(r27=cython.double)
    @cython.locals(r28=cython.double)
    @cython.locals(r29=cython.double)
    @cython.locals(r30=cython.double)
    @cython.locals(r31=cython.double)
    @cython.locals(x0=cython.double, y0=cython.double)
    @cython.locals(x1=cython.double, y1=cython.double)
    @cython.locals(x2=cython.double, y2=cython.double)
    def _qCurveToOne(self, p1, p2):
        x0, y0 = self._getCurrentPoint()
        x1, y1 = p1
        x2, y2 = p2

        r0 = x1**5
        r1 = x2**5
        r2 = 5 * y2
        r3 = x2**4
        r4 = 42 * r3 * x1
        r5 = x2**2
        r6 = x1**3
        r7 = 56 * r6
        r8 = r5 * r7
        r9 = x1**4
        r10 = 2 * y1
        r11 = 7 * y2
        r12 = x2**3
        r13 = x1**2
        r14 = 56 * r13
        r15 = r12 * r14
        r16 = x2 * y2
        r17 = 30 * x1
        r18 = r17 * y0
        r19 = x1 * y1
        r20 = x1 * y2
        r21 = 40 * r9
        r22 = 56 * y0
        r23 = 28 * r19
        r24 = 28 * x1
        r25 = r13 * y0
        r26 = r13 * y1
        r27 = 7 * y0
        r28 = r6 * y0
        r29 = r12 * y0
        r30 = r5 * y2
        r31 = 24 * r26

        self.momentX4 += (
            8 * r0 * y2 / 3465
            - r1 * y1 / 33
            - r1 * y2 / 6
            - r15 * (r10 - 3 * y2) / 6930
            - r4 * (-r2 + 4 * y1) / 6930
            - r8 * (y1 - 2 * y2) / 6930
            - 4 * r9 * x2 * (r10 - r11) / 3465
            + x0**5 * (55 * y0 + 10 * y1 + y2) / 330
            + x0**4 * (r10 * x2 + r16 - r18 + 24 * r19 + 6 * r20 - 3 * x2 * y0) / 990
            + x0**3
            * (
                r10 * r5
                + r14 * y2
                + r16 * r24
                + r2 * r5
                - r22 * x1 * x2
                + r23 * x2
                - 168 * r25
                + 112 * r26
                - r27 * r5
            )
            / 6930
            + x0**2
            * (
                -r10 * r12
                + r11 * r12
                + 60 * r13 * r16
                + r17 * r30
                - r18 * r5
                - 84 * r25 * x2
                - 112 * r28
                - 5 * r29
                + r31 * x2
                + r7 * y1
                + r7 * y2
            )
            / 6930
            - x0
            * (
                -56 * r12 * r20
                + r12 * r23
                - 84 * r13 * r30
                - 80 * r16 * r6
                - r21 * y2
                + r22 * r9
                + r24 * r29
                + 60 * r25 * r5
                + r27 * r3
                + 80 * r28 * x2
                + 14 * r3 * y1
                - 21 * r3 * y2
                + r31 * r5
                - 16 * r9 * y1
            )
            / 6930
            - y0 * (16 * r0 + 21 * r1 + r15 + r21 * x2 + r4 + r8) / 6930
        )

    @cython.locals(r0=cython.double)
    @cython.locals(r1=cython.double)
    @cython.locals(r2=cython.double)
    @cython.locals(r3=cython.double)
    @cython.locals(r4=cython.double)
    @cython.locals(r5=cython.double)
    @cython.locals(r6=cython.double)
    @cython.locals(r7=cython.double)
    @cython.locals(r8=cython.double)
    @cython.locals(r9=cython.double)
    @cython.locals(r10=cython.double)
    @cython.locals(r11=cython.double)
    @cython.locals(r12=cython.double)
    @cython.locals(r13=cython.double)
    @cython.locals(r14=cython.double)
    @cython.locals(r15=cython.double)
    @cython.locals(r16=cython.double)
    @cython.locals(r17=cython.double)
    @cython.locals(r18=cython.double)
    @cython.locals(r19=cython.double)
    @cython.locals(r20=cython.double)
    @cython.locals(r21=cython.double)
    @cython.locals(r22=cython.double)
    @cython.locals(r23=cython.double)
    @cython.locals(r24=cython.double)
    @cython.locals(r25=cython.double)
    @cython.locals(r26=cython.double)
    @cython.locals(r27=cython.double)
    @cython.locals(r28=cython.double)
    @cython.locals(r29=cython.double)
    @cython.locals(r30=cython.double)
    @cython.locals(r31=cython.double)
    @cython.locals(r32=cython.double)
    @cython.locals(r33=cython.double)
    @cython.locals(r34=cython.double)
    @cython.locals(r35=cython.double)
    @cython.locals(r36=cython.double)
    @cython.locals(r37=cython.double)
    @cython.locals(r38=cython.double)
    @cython.locals(r39=cython.double)
    @cython.locals(r40=cython.double)
    @cython.locals(r41=cython.double)
    @cython.locals(r42=cython.double)
    @cython.locals(r43=cython.double)
    @cython.locals(r44=cython.double)
    @cython.locals(r45=cython.double)
    @cython.locals(r46=cython.double)
    @cython.locals(r47=cython.double)
    @cython.locals(r48=cython.double)
    @cython.locals(r49=cython.double)
    @cython.locals(r50=cython.double)
    @cython.locals(r51=cython.double)
    @cython.locals(r52=cython.double)
    @cython.locals(r53=cython.double)
    @cython.locals(r54=cython.double)
    @cython.locals(r55=cython.double)
    @cython.locals(r56=cython.double)
    @cython.locals(r57=cython.double)
    @cython.locals(r58=cython.double)
    @cython.locals(r59=cython.double)
    @cython.locals(r60=cython.double)
    @cython.locals(r61=cython.double)
    @cython.locals(r62=cython.double)
    @cython.locals(r63=cython.double)
    @cython.locals(r64=cython.double)
    @cython.locals(r65=cython.double)
    @cython.locals(r66=cython.double)
    @cython.locals(r67=cython.double)
    @cython.locals(r68=cython.double)
    @cython.locals(r69=cython.double)
    @cython.locals(r70=cython.double)
    @cython.locals(r71=cython.double)
    @cython.locals(r72=cython.double)
    @cython.locals(r73=cython.double)
    @cython.locals(r74=cython.double)
    @cython.locals(r75=cython.double)
    @cython.locals(r76=cython.double)
    @cython.locals(r77=cython.double)
    @cython.locals(r78=cython.double)
    @cython.locals(r79=cython.double)
    @cython.locals(r80=cython.double)
    @cython.locals(r81=cython.double)
    @cython.locals(r82=cython.double)
    @cython.locals(r83=cython.double)
    @cython.locals(r84=cython.double)
    @cython.locals(r85=cython.double)
    @cython.locals(r86=cython.double)
    @cython.locals(r87=cython.double)
    @cython.locals(r88=cython.double)
    @cython.locals(r89=cython.double)
    @cython.locals(r90=cython.double)
    @cython.locals(r91=cython.double)
    @cython.locals(r92=cython.double)
    @cython.locals(r93=cython.double)
    @cython.locals(r94=cython.double)
    @cython.locals(r95=cython.double)
    @cython.locals(r96=cython.double)
    @cython.locals(r97=cython.double)
    @cython.locals(x0=cython.double, y0=cython.double)
    @cython.locals(x1=cython.double, y1=cython.double)
    @cython.locals(x2=cython.double, y2=cython.double)
    @cython.locals(x3=cython.double, y3=cython.double)
    def _curveToOne(self, p1, p2, p3):
        x0, y0 = self._getCurrentPoint()
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3

        r0 = x2**5
        r1 = x3**5
        r2 = x1**5
        r3 = 15 * y2
        r4 = 7 * y3
        r5 = 3 * y2
        r6 = x3**4
        r7 = r6 * x2
        r8 = x2**4
        r9 = r8 * x3
        r10 = x3**3
        r11 = x2**2
        r12 = r10 * r11
        r13 = x3**2
        r14 = x2**3
        r15 = r13 * r14
        r16 = x1**4
        r17 = x2 * y1
        r18 = x2 * y2
        r19 = 126 * r18
        r20 = x2 * y3
        r21 = x3 * y1
        r22 = 28 * y3
        r23 = 4455 * r9
        r24 = x1 * y0
        r25 = x1 * y2
        r26 = x1 * y3
        r27 = x2 * y0
        r28 = 42 * y2
        r29 = x3 * y3
        r30 = x1**3
        r31 = 210 * r29 * x2
        r32 = r11 * y1
        r33 = r11 * y2
        r34 = r11 * y3
        r35 = r13 * y1
        r36 = 55 * r13
        r37 = x1**2
        r38 = r14 * y1
        r39 = r14 * y2
        r40 = r14 * y3
        r41 = r10 * y1
        r42 = r10 * y3
        r43 = r35 * x2
        r44 = r32 * x3
        r45 = r33 * x3
        r46 = r8 * y2
        r47 = 4455 * y3
        r48 = r6 * y1
        r49 = r6 * y2
        r50 = r6 * y3
        r51 = r41 * x2
        r52 = r10 * r18
        r53 = r42 * x2
        r54 = r11 * r35
        r55 = r13 * r34
        r56 = r24 * x2
        r57 = r20 * x1
        r58 = r18 * x3
        r59 = r37 * y0
        r60 = r37 * y1
        r61 = r37 * y2
        r62 = r37 * y3
        r63 = r11 * y0
        r64 = 6804 * x1
        r65 = 13365 * r16
        r66 = x1 * x2
        r67 = 11340 * x1
        r68 = r67 * x3
        r69 = x2 * x3
        r70 = 9072 * r69
        r71 = 13608 * r37
        r72 = 1512 * r13
        r73 = 8910 * x1
        r74 = r37 * x2
        r75 = r30 * y0
        r76 = r30 * y1
        r77 = r30 * y2
        r78 = r30 * y3
        r79 = r14 * y0
        r80 = r10 * y0
        r81 = 2835 * y3
        r82 = 315 * r13
        r83 = 252 * r13
        r84 = 23166 * y0
        r85 = 5346 * y1
        r86 = r59 * x3
        r87 = 945 * x3
        r88 = r13 * r18
        r89 = 756 * x3
        r90 = 2268 * r8
        r91 = 9072 * x1
        r92 = 11340 * x2
        r93 = 5940 * x3
        r94 = 1620 * x3
        r95 = 4536 * x3
        r96 = 3024 * x3
        r97 = 1890 * r13

        self.momentX4 += (
            81 * r0 * y3 / 61880
            - r1 * y2 / 34
            - r1 * y3 / 6
            - 3 * r12 * (r5 - 5 * y3) / 680
            - 9 * r15 * (-r4 + r5) / 4760
            + 27
            * r16
            * (-45 * r17 + r19 + 84 * r20 - 21 * r21 + r22 * x3 + 28 * x3 * y2)
            / 1361360
            + 81 * r2 * (r3 + r4) / 1361360
            + 9
            * r30
            * (
                r13 * r3
                + r19 * x3
                - 168 * r21 * x2
                + r31
                - 189 * r32
                + 252 * r33
                + 252 * r34
                - 42 * r35
                + r36 * y3
            )
            / 680680
            + 3
            * r37
            * (
                -66 * r10 * y2
                + 990 * r13 * r20
                + 1485 * r34 * x3
                - 756 * r38
                + 567 * r39
                + 945 * r40
                - 165 * r41
                + 286 * r42
                - 675 * r43
                - 1134 * r44
                + 405 * r45
            )
            / 680680
            - r7 * (r5 - 4 * y3) / 136
            - 27 * r9 * (r5 - 13 * y3) / 61880
            + x0**5 * (r3 + 680 * y0 + 120 * y1 + y3) / 4080
            + x0**4
            * (
                819 * r17
                + 468 * r18
                + 78 * r20
                + 39 * r21
                - 10920 * r24
                + 2457 * r25
                + 273 * r26
                - 1365 * r27
                + r28 * x3
                + 10 * r29
                + 8190 * x1 * y1
                - 91 * x3 * y0
            )
            / 371280
            + x0**3
            * (
                r13 * r22
                + r13 * r28
                + 7722 * r17 * x1
                + 8316 * r18 * x1
                + 396 * r21 * x1
                - 1716 * r24 * x3
                + 990 * r25 * x3
                - 660 * r27 * x3
                + 330 * r29 * x1
                + r31
                + 594 * r32
                + 1485 * r33
                + 495 * r34
                - 15 * r35
                - r36 * y0
                - 18018 * r56
                + 1980 * r57
                + 450 * r58
                - 45045 * r59
                + 27027 * r60
                + 15444 * r61
                + 2574 * r62
                - 2574 * r63
            )
            / 2042040
            + x0**2
            * (
                r10 * r3
                + r11 * r81 * x1
                + r20 * r82
                - 810 * r21 * r66
                - 2970 * r24 * r69
                - r24 * r82
                + r25 * r83
                + r26 * r83
                - r27 * r83
                + 1512 * r29 * r66
                + r33 * r89
                + 6075 * r33 * x1
                + r34 * r89
                - 189 * r35 * x1
                - 405 * r38
                + 1134 * r39
                + 756 * r40
                - 42 * r41
                + 55 * r42
                - 252 * r43
                - 567 * r44
                + r47 * r74
                + 2268 * r58 * x1
                + 13365 * r61 * x2
                + 2025 * r61 * x3
                + r62 * r87
                - r63 * r73
                - r63 * r87
                - r74 * r84
                + r74 * r85
                - 27027 * r75
                + 11583 * r76
                + 12474 * r77
                + 2970 * r78
                - 1485 * r79
                - 28 * r80
                - 2970 * r86
                + 189 * r88
            )
            / 2042040
            - x0
            * (
                26730 * r11 * r59
                + 3024 * r13 * r56
                - 5940 * r13 * r57
                - 1134 * r13 * r61
                - r16 * r47
                + r16 * r84
                - r16 * r85
                + 7290 * r32 * r37
                - 20412 * r33 * r37
                - r34 * r68
                - r34 * r71
                + 4536 * r35 * r66
                + r38 * r64
                + r38 * r95
                - r39 * r91
                - r39 * r94
                - r40 * r91
                - r40 * r93
                + 900 * r41 * x1
                - 1320 * r42 * x1
                + r44 * r91
                - r45 * r64
                - 1701 * r46
                + 462 * r48
                + 429 * r49
                - 1001 * r50
                + 1980 * r51
                + 792 * r52
                - 3432 * r53
                + 4050 * r54
                - 5940 * r55
                + r59 * r72
                + 110 * r6 * y0
                + 6804 * r60 * r69
                + r60 * r72
                - r61 * r70
                - r62 * r70
                - r62 * r97
                + r63 * r91 * x3
                + r63 * r97
                - r65 * y2
                + r67 * r79
                + r75 * r93
                + 35640 * r75 * x2
                + r76 * r94
                - r77 * r95
                - 24300 * r77 * x2
                - r78 * r92
                - r78 * r96
                + r79 * r96
                - r8 * r81
                + 420 * r80 * x1
                + 660 * r80 * x2
                + r86 * r92
                - 1620 * r88 * x1
                + r90 * y0
                + r90 * y1
            )
            / 4084080
            - x1
            * (
                3564 * r13 * r33
                + 8100 * r38 * x3
                - 11880 * r40 * x3
                - 1215 * r46
                - r47 * r8
                + 1716 * r48
                + 3003 * r49
                - 5005 * r50
                + 5544 * r51
                + 5148 * r52
                - 12012 * r53
                + 8910 * r54
                - 15444 * r55
                + 3402 * r8 * y1
            )
            / 1361360
            - y0
            * (
                1701 * r0
                + 1001 * r1
                + 990 * r10 * r37
                + 3960 * r10 * r66
                + r11 * r13 * r73
                + 17010 * r11 * r30
                + r11 * r71 * x3
                + 5148 * r12
                + 5670 * r13 * r74
                + r14 * r68
                + r14 * r71
                + 5940 * r15
                + 2835 * r16 * x3
                + 5346 * r2
                + r23
                + r30 * r70
                + r30 * r72
                + 858 * r6 * x1
                + r64 * r8
                + r65 * x2
                + 3003 * r7
            )
            / 4084080
            - y1
            * (1215 * r0 + 5005 * r1 + 10296 * r12 + 8316 * r15 + r23 + 9009 * r7)
            / 1361360
        )


if __name__ == "__main__":
    from fontTools.misc.symfont import x, y, printGreenPen

    printGreenPen(
        "MomentX4Pen",
        [
            ("momentX4", x**4),
        ],
    )
