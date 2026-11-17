"""Plot avar structure and the mapped image of a public-input slice."""

import math

from .analyze import analyze, contours
from .map import ForwardMapper, _load_font, _parse_coordinates


def _boundaryLines(report, axes, location):
    """Intersect analyze()'s candidate boundary patches with a two-axis slice."""
    lines = set()
    for boundary in report["boundaries"]:
        tag = boundary["axis"]
        if tag not in axes:
            continue
        ranges = boundary.get("ranges", {})
        if any(
            t not in axes
            and not any(
                a <= location.get(t, report["axes"][t]["default"]) <= b
                for a, b in intervals
            )
            for t, intervals in ranges.items()
        ):
            continue
        other = axes[1] if tag == axes[0] else axes[0]
        domain = report["axes"][other]
        for a, b in ranges.get(other, [[domain["minimum"], domain["maximum"]]]):
            v = boundary["value"]
            lines.add(((v, a), (v, b)) if tag == axes[0] else ((a, v), (b, v)))
    return sorted(lines)


def plot(
    font, axes, *, output=None, location=None, samples=33, levels=None, figure=None
):
    """Return a Matplotlib figure for a one- or two-axis slice.

    Calls analyze() for structural boundaries, contours() for continuous
    output level sets, and ForwardMapper for rounded/clipped mapped samples.
    Hidden inputs and other unspecified inputs stay at default. Input axes
    use user units; colors and projected outputs use normalized units.

    The mapped grid shows the image of this slice projected onto two output
    axes. It is sampled geometry, not a certificate of global reachability.
    """
    import numpy as np
    from matplotlib import pyplot
    from matplotlib.collections import LineCollection
    from matplotlib.colors import Normalize

    axes = tuple(axes)
    location = dict(location or {})
    output = output or (axes[0] if axes else "")
    report = analyze(font)
    # Reuse contour validation, including hidden-input constraints and jumps.
    contours(font, axes, output, 0, location=location, samples=samples)
    projection = None
    if len(axes) == 2:
        projection = (axes[0], output if output != axes[0] else axes[1])
        for tag in projection:
            if tag != output:
                contours(font, axes, tag, 0, location=location, samples=samples)
    grids = []
    for tag in axes:
        metadata = report["axes"][tag]
        grids.append(
            sorted(
                set(metadata["knots"])
                | set(np.linspace(metadata["minimum"], metadata["maximum"], samples))
            )
        )
    if math.prod(map(len, grids)) > 65536:
        raise ValueError("Plot grid exceeds 65536 points after adding avar knots")
    mapper = ForwardMapper(font)
    if figure is None:
        figure = pyplot.figure(figsize=(11, 5), layout="constrained")
    if len(axes) == 1:
        subplot = figure.add_subplot(111)
        x = grids[0]
        y = [
            mapper.map({**location, axes[0]: value}, outputNormalized=True)[output]
            for value in x
        ]
        subplot.plot(x, y)
        for boundary in report["boundaries"]:
            if boundary["axis"] == axes[0]:
                subplot.axvline(
                    boundary["value"], color="0.5", alpha=0.3, linewidth=0.8
                )
        subplot.set(
            xlabel=f"{axes[0]} input (user units)",
            ylabel=f"{output} output (normalized)",
        )
    else:
        x, y = grids
        mapped = [
            [
                mapper.map({**location, axes[0]: a, axes[1]: b}, outputNormalized=True)
                for a in x
            ]
            for b in y
        ]
        color = np.array([[point[output] for point in row] for row in mapped])
        lo, hi = float(color.min()), float(color.max())
        if lo == hi:
            lo, hi = lo - 0.5, hi + 0.5
        norm = Normalize(lo, hi)
        left, right = figure.subplots(1, 2)
        heatmap = left.pcolormesh(
            x, y, color, shading="gouraud", cmap="viridis", norm=norm
        )
        boundaries = _boundaryLines(report, axes, location)
        left.add_collection(
            LineCollection(boundaries, colors="0.3", linewidths=0.7, alpha=0.5)
        )
        if levels is None:
            levels = (
                np.linspace(float(color.min()), float(color.max()), 7)[1:-1]
                if color.min() != color.max()
                else []
            )
        for level in levels:
            geometry = contours(
                font, axes, output, float(level), location=location, samples=samples
            )
            left.add_collection(
                LineCollection(geometry["lines"], colors="white", linewidths=1.2)
            )
            if geometry["points"]:
                points = np.array(geometry["points"])
                left.scatter(points[:, 0], points[:, 1], c="white", s=15)
            for line in geometry["lines"]:
                point = line[len(line) // 2]
                left.annotate(f"{level:.2g}", point, color="white", fontsize="small")
        left.set(
            xlabel=f"{axes[0]} input (user units)",
            ylabel=f"{axes[1]} input (user units)",
            title="Input slice · structural boundaries and contours",
        )
        segments, colors = [], []
        for j, row in enumerate(mapped):
            for i, point in enumerate(row):
                for ni, nj in ((i + 1, j), (i, j + 1)):
                    if ni >= len(x) or nj >= len(y):
                        continue
                    other = mapped[nj][ni]
                    segments.append(
                        [
                            (point[projection[0]], point[projection[1]]),
                            (other[projection[0]], other[projection[1]]),
                        ]
                    )
                    colors.append((point[output] + other[output]) / 2)
        grid = LineCollection(
            segments, cmap="viridis", norm=norm, linewidths=0.65, alpha=0.7
        )
        grid.set_array(np.array(colors))
        right.add_collection(grid)
        right.autoscale()
        right.set(
            xlabel=f"{projection[0]} output (normalized)",
            ylabel=f"{projection[1]} output (normalized)",
            title="Mapped grid · projection of this slice",
        )
        figure.colorbar(
            heatmap, ax=[left, right], label=f"{output} output (normalized)", shrink=0.8
        )
    fixed = ", ".join(f"{tag}={value:g}" for tag, value in location.items())
    subtitle = (
        f"{fixed}; other inputs at default" if fixed else "Other inputs at default"
    )
    figure.suptitle(f"avar: {' × '.join(axes)} → {output}\n{subtitle}")
    return figure


def main(args=None):
    """Plot avar structure, level curves, and the mapped image of a slice."""
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.avar.plot", description=main.__doc__
    )
    parser.add_argument("font")
    parser.add_argument("axes", nargs="+", help="One or two public input axis tags")
    parser.add_argument(
        "--output", help="Output axis to plot/color, including hidden axes"
    )
    parser.add_argument(
        "--at",
        action="append",
        default=[],
        metavar="AXIS=value",
        help="Fix another input in user units",
    )
    parser.add_argument("--samples", type=int, default=33)
    parser.add_argument("--levels", help="Comma-separated normalized contour levels")
    parser.add_argument(
        "-o", "--output-file", help="Save a figure instead of opening a window"
    )
    options = parser.parse_args(args)
    font = _load_font(parser, options.font)
    try:
        from matplotlib import pyplot

        figure = plot(
            font,
            options.axes,
            output=options.output,
            location=_parse_coordinates(parser, options.at),
            samples=options.samples,
            levels=(
                None
                if options.levels is None
                else [float(v) for v in options.levels.split(",")]
            ),
        )
    except (ValueError, ImportError) as e:
        parser.error(str(e))
    if options.output_file:
        figure.savefig(options.output_file, dpi=160)
    else:
        pyplot.show()


if __name__ == "__main__":
    main()
