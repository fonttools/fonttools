"""Draw statistical shape of a glyph as an ellipse."""

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.cairoPen import CairoPen
from fontTools.pens.statisticsPen import StatisticsPen
import cairo
import math
import sys


font = TTFont(sys.argv[1])
unicode = sys.argv[2]

cmap = font['cmap'].getBestCmap()
gid = cmap[ord(unicode)]

hhea = font['hhea']
glyphset = font.getGlyphSet()
with cairo.SVGSurface("example.svg", hhea.advanceWidthMax, hhea.ascent-hhea.descent) as surface:
    context = cairo.Context(surface)
    context.translate(0, +font['hhea'].ascent)
    context.scale(1, -1)

    glyph = glyphset[gid]

    recording = RecordingPen()
    glyph.draw(recording)

    context.translate((hhea.advanceWidthMax - glyph.width) * .5, 0)

    pen = CairoPen(glyphset, context)
    glyph.draw(pen)
    context.fill()

    stats = StatisticsPen()
    glyph.draw(stats)

    context.save()

    # https://cookierobotics.com/007/
    a = stats.varianceX
    b = stats.covariance
    c = stats.varianceY
    delta = (((a - c) * .5) ** 2 + b * b) ** .5
    lambda1 = (a + c) * .5 + delta  # Major eigenvalue
    lambda2 = (a + c) * .5 - delta  # Minor eigenvalue
    theta = (
             math.atan2(lambda1 - a, b)
             if b != 0 else
             (math.pi * .5 if a < c else 0)
            )
    mult = 4  # Empirical by drawing '.'
    transform = cairo.Matrix()
    transform.translate(stats.meanX, stats.meanY)
    transform.rotate(theta)
    transform.scale(math.sqrt(lambda1), math.sqrt(lambda2))
    transform.scale(mult, mult)

    ellipse_area = math.sqrt(lambda1) * math.sqrt(lambda2) * math.pi/4 * mult * mult

    context.set_line_cap(cairo.LINE_CAP_ROUND)
    context.transform(transform)
    context.move_to(0, 0)
    context.line_to(0, 0)
    context.set_line_width(1)
    context.set_source_rgba(1, 0, 0, abs(stats.area / ellipse_area))
    context.stroke()

    context.restore()
