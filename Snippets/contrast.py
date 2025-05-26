import numpy as np
import argparse
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
        transform = (
            Identity
            .translate(-centroid_x, -centroid_y)
            .rotate(np.deg2rad(angle))
        )

        pen_rot = StatisticsPen()
        glyph.draw(TransformPen(pen_rot, transform))

        varX = pen_rot.varianceX
        varY = pen_rot.varianceY

        if min(varX, varY) < 1e-6:
            contrast = np.inf
        else:
            contrast = max(varX, varY) / min(varX, varY)

        contrast_ratios.append((angle, contrast))

    best_angle, max_contrast = max(contrast_ratios, key=lambda x: x[1])

    return best_angle, max_contrast, contrast_ratios


def main():
    parser = argparse.ArgumentParser(description="Analyze glyph stroke contrast.")
    parser.add_argument("fontfile", help="Path to the font file (.ttf, .otf)")
    parser.add_argument("-c", "--char", default="o", help="Character to analyze (default: 'o')")
    parser.add_argument("-s", "--step", type=float, default=1, help="Angle step in degrees (default: 1)")
    parser.add_argument("-p", "--plot", action="store_true", help="Plot contrast ratios with matplotlib")

    args = parser.parse_args()

    font = TTFont(args.fontfile)
    cmap = font.getBestCmap()
    if ord(args.char) not in cmap:
        raise ValueError(f"Character '{args.char}' not found in font cmap.")

    glyphname = cmap[ord(args.char)]
    glyfSet = font.getGlyphSet()
    glyph = glyfSet[glyphname]

    angle, contrast, all_ratios = glyph_contrast_centered(glyph, args.step)

    print(f"Glyph '{glyphname}' (char '{args.char}'): max contrast at angle {angle}°, contrast ratio: {contrast:.2f}")

    if args.plot:
        import matplotlib.pyplot as plt

        angles, contrasts = zip(*all_ratios)
        plt.figure(figsize=(8, 4))
        plt.plot(angles, contrasts, '-o')
        plt.xlabel("Angle (degrees)")
        plt.ylabel("Contrast ratio")
        plt.title(f"Glyph '{glyphname}' Contrast Analysis")
        plt.grid(True)
        plt.axvline(angle, color='r', linestyle='--', label=f"Max contrast: {angle}°")
        plt.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()

