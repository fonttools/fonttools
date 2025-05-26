import numpy as np
import argparse
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

    angles = np.arange(0, 180, angle_step)
    contrast_ratios = []

    for angle in angles:
        transform = (
            Identity
            .translate(-centroid_x, -centroid_y)
            .rotate(np.deg2rad(-angle))  # rotate by negative of angle
        )
        pen_rot = StatisticsPen()
        glyph.draw(TransformPen(pen_rot, transform))
        varX = pen_rot.varianceX

        contrast_ratios.append((angle, varX))

    best_angle, max_contrast = max(contrast_ratios, key=lambda x: x[1])
    worst_angle, min_contrast = min(contrast_ratios, key=lambda x: x[1])

    return best_angle, max_contrast, worst_angle, min_contrast, contrast_ratios, (centroid_x, centroid_y)


def generate_svg(glyph, centroid, angles, colors, contrast_ratios, filename="glyph.svg"):
    svg_pen = SVGPathPen(None)
    length = glyph.width * 1.5

    transform = (
        Identity
        .scale(1, -1)
        .translate(-centroid[0], -centroid[1])
    )
    glyph.draw(TransformPen(svg_pen, transform))
    path_data = svg_pen.getCommands()

    svg_lines = ""
    for angle, color in zip(angles, colors):
        angle = -angle
        dx = np.cos(np.deg2rad(angle)) * length / 2
        dy = np.sin(np.deg2rad(angle)) * length / 2
        svg_lines += f"<line x1='{-dx}' y1='{-dy}' x2='{dx}' y2='{dy}' stroke='{color}' stroke-width='10'/>\n"

    # Add contrast plot
    plot_height = 100
    plot_width = 180
    plot_lines = []
    max_contrast = max(c for _, c in contrast_ratios if np.isfinite(c))
    for angle, contrast in contrast_ratios:
        if np.isinf(contrast):
            continue
        x = angle / 180 * plot_width - length / 2
        y = -length / 2 - (contrast / max_contrast * plot_height)
        plot_lines.append((x, y))

    contrast_path = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in plot_lines)
    svg_plot = f"<path d='{contrast_path}' fill='none' stroke='blue' stroke-width='2'/>"

    svg_content = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='{-length/2} {-length/2 - plot_height} {length} {length + plot_height}'>
    <g>
        <path d='{path_data}' fill='black' stroke='black'/>
        {svg_lines.strip()}
        {svg_plot}
    </g>
</svg>"""

    with open(filename, "w") as f:
        f.write(svg_content)


def main():
    parser = argparse.ArgumentParser(description="Analyze glyph stroke contrast.")
    parser.add_argument("fontfile", help="Path to the font file (.ttf, .otf)")
    parser.add_argument("-c", "--char", default="o", help="Character to analyze (default: 'o')")
    parser.add_argument("-s", "--step", type=float, default=1, help="Angle step in degrees (default: 1)")
    parser.add_argument("-o", "--output", default="glyph.svg", help="Output SVG file")

    args = parser.parse_args()

    font = TTFont(args.fontfile)
    cmap = font.getBestCmap()
    if ord(args.char) not in cmap:
        raise ValueError(f"Character '{args.char}' not found in font cmap.")

    glyphname = cmap[ord(args.char)]
    glyfSet = font.getGlyphSet()
    glyph = glyfSet[glyphname]

    best_angle, max_contrast, worst_angle, min_contrast, contrast_ratios, centroid = glyph_contrast_centered(glyph, args.step)

    print(f"Glyph '{glyphname}' (char '{args.char}'):\n  Max spread at angle {best_angle}°, varX: {max_contrast:.2f}\n  Min spread at angle {worst_angle}°, varX: {min_contrast:.2f}")

    generate_svg(glyph, centroid, [best_angle, worst_angle], ["red", "purple"], contrast_ratios, args.output)
    print(f"SVG saved as '{args.output}'")


if __name__ == "__main__":
    main()

