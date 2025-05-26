import numpy as np
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.misc.transform import Identity


def glyph_contrast_centered(glyph, angle_step=1):
    # First, compute centroid at 0°
    pen = StatisticsPen()
    glyph.draw(pen)

    centroid_x = pen.meanX
    centroid_y = pen.meanY

    angles = np.arange(0, 180, angle_step)
    contrast_ratios = []

    for angle in angles:
        # Translate to centroid, then rotate
        transform = (
            Identity
            .translate(-centroid_x, -centroid_y)
            .rotate(np.deg2rad(angle))
        )

        # Apply transform
        pen_rot = StatisticsPen()
        glyph.draw(TransformPen(pen_rot, transform))

        varX = pen_rot.varianceX
        varY = pen_rot.varianceY

        # Avoid numerical instability
        if min(varX, varY) < 1e-6:
            contrast = np.inf
        else:
            contrast = max(varX, varY) / min(varX, varY)

        contrast_ratios.append((angle, contrast))

        # Optional debug:
        # print(f"{angle:3}° | varX: {varX:8.2f}, varY: {varY:8.2f}, contrast: {contrast:.2f}")

    # Find best angle
    best_angle, max_contrast = max(contrast_ratios, key=lambda x: x[1])

    return best_angle, max_contrast, contrast_ratios


if __name__ == "__main__":
    # Example usage
    from fontTools.ttLib import TTFont
    import sys

    font = TTFont(sys.argv[1])
    char = 'o' if len(sys.argv) < 3 else sys.argv[2]
    glyphname = font['cmap'].getBestCmap()[ord(char)]
    glyfSet = font.getGlyphSet()
    glyph = glyfSet[glyphname]

    angle, contrast, all_ratios = glyph_contrast_centered(glyph)

    print(f"Max contrast at angle {angle}°, contrast ratio: {contrast:.2f}")

