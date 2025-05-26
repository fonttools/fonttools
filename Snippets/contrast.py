import numpy as np
import argparse
from momentX4 import MomentX4Pen
from functools import partial
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.misc.transform import Identity
from fontTools.pens.svgPathPen import SVGPathPen


def glyph_contrast_centered(glyph, angle_step=1):
    pen = StatisticsPen()
    glyph.draw(pen)

    centroid_x = pen.meanX
    centroid_y = pen.meanY

    angles = np.arange(0, 360, angle_step)
    contrast_ratios = []

    for angle in angles:
        transform = Identity.rotate(np.deg2rad(-angle)).translate(
            -centroid_x, -centroid_y
        )
        pen_rot = StatisticsPen()
        glyph.draw(TransformPen(pen_rot, transform))
        area = pen_rot.area
        varX = pen_rot.varianceX

        momentX4_pen = MomentX4Pen()
        glyph.draw(TransformPen(momentX4_pen, transform))
        momentX4 = momentX4_pen.momentX4 / area

        contrast = momentX4 / (varX**2) if varX > 0 else np.inf

        contrast_ratios.append((angle, contrast))

    best_angle, max_contrast = max(contrast_ratios, key=lambda x: x[1])
    worst_angle, min_contrast = min(contrast_ratios, key=lambda x: x[1])

    return (
        best_angle,
        max_contrast,
        worst_angle,
        min_contrast,
        contrast_ratios,
        (centroid_x, centroid_y),
    )


def generate_svg(
    glyph, centroid, angles, colors, contrast_ratios, filename="glyph.svg"
):
    svg_pen = SVGPathPen(None)
    length = glyph.width * 1.5

    transform = Identity.scale(1, -1).translate(-centroid[0], -centroid[1])
    glyph.draw(TransformPen(svg_pen, transform))
    path_data = svg_pen.getCommands()

    svg_lines = ""
    for angle, color in zip(angles, colors):
        angle = -angle + 90
        dx = np.cos(np.deg2rad(angle)) * length / 2
        dy = np.sin(np.deg2rad(angle)) * length / 2
        svg_lines += f"<line x1='{-dx}' y1='{-dy}' x2='{dx}' y2='{dy}' stroke='{color}' stroke-width='10'/>\n"

    # Polar contrast plot
    finite_contrasts = [c for _, c in contrast_ratios if np.isfinite(c)]
    if finite_contrasts:
        max_contrast = max(finite_contrasts)
    else:
        max_contrast = 1.0

    polar_path = []
    for angle, contrast in contrast_ratios:
        if not np.isfinite(contrast):
            continue
        radius = contrast / max_contrast * (length / 2)
        theta = np.deg2rad(-angle + 90)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        polar_path.append((x, y))

    contrast_polar_path = (
        "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in polar_path) + " Z"
    )
    svg_polar = (
        f"<path d='{contrast_polar_path}' fill='none' stroke='blue' stroke-width='2'/>"
    )

    svg_content = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='{-length/2} {-length/2} {length} {length}'>
    <g>
        <path d='{path_data}' fill='black' stroke='black'/>
        {svg_lines.strip()}
        {svg_polar}
    </g>
</svg>"""

    with open(filename, "w") as f:
        f.write(svg_content)


def main():
    parser = argparse.ArgumentParser(description="Analyze glyph stroke contrast.")
    parser.add_argument("fontfile", help="Path to the font file (.ttf, .otf)")
    parser.add_argument(
        "-c", "--char", default="o", help="Character to analyze (default: 'o')"
    )
    parser.add_argument(
        "-s", "--step", type=float, default=1, help="Angle step in degrees (default: 1)"
    )
    parser.add_argument("-o", "--output", default="glyph.svg", help="Output SVG file")

    args = parser.parse_args()

    font = TTFont(args.fontfile)
    glyfSet = font.getGlyphSet()

    glyphname = args.char
    if glyphname not in glyfSet:
        cmap = font.getBestCmap()
        if ord(args.char) not in cmap:
            raise ValueError(f"Character '{args.char}' not found in font cmap.")
        glyphname = cmap[ord(glyphname)]

    glyph = glyfSet[glyphname]

    best_angle, max_contrast, worst_angle, min_contrast, contrast_ratios, centroid = (
        glyph_contrast_centered(glyph, args.step)
    )

    print(
        f"Glyph '{glyphname}' (char '{args.char}'):\n  Max at angle {best_angle}°, ratio: {max_contrast:.2f}\n  Min at angle {worst_angle}°, ratio: {min_contrast:.2f}"
    )

    generate_svg(
        glyph,
        centroid,
        [best_angle, worst_angle],
        ["red", "purple"],
        contrast_ratios,
        args.output,
    )
    print(f"SVG saved as '{args.output}'")


if __name__ == "__main__":
    main()
