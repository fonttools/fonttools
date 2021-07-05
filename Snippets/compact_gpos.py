#! /usr/bin/env python3

"""
Sample script to use the otlLib.optimize.gpos functions to compact GPOS tables
of existing fonts. This script takes one or more TTF files as arguments and
will create compacted copies of the fonts using all available modes of the GPOS
compaction algorithm. For each copy, it will measure the new size of the GPOS
table and also the new size of the font in WOFF2 format. All results will be
printed to stdout in CSV format, so the savings provided by the algorithm in
each mode can be inspected.

This was initially made to debug the algorithm but can also be used to choose
a mode value for a specific font (trade-off between bytes saved in TTF format
vs more bytes in WOFF2 format and more subtables).

Run:

python Snippets/compact_gpos.py MyFont.ttf > results.csv
"""

import argparse
from collections import defaultdict
import csv
import time
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from fontTools.ttLib import TTFont
from fontTools.otlLib.optimize import compact

MODES = [str(c) for c in range(1, 10)]


def main(args: Optional[List[str]] = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("fonts", type=Path, nargs="+", help="Path to TTFs.")
    parsed_args = parser.parse_args(args)

    runtimes = defaultdict(list)
    rows = []
    font_path: Path
    for font_path in parsed_args.fonts:
        font = TTFont(font_path)
        if "GPOS" not in font:
            print(f"No GPOS in {font_path.name}, skipping.", file=sys.stderr)
            continue
        size_orig = len(font.getTableData("GPOS")) / 1024
        print(f"Measuring {font_path.name}...", file=sys.stderr)

        fonts = {}
        font_paths = {}
        sizes = {}
        for mode in MODES:
            print(f"    Running mode={mode}", file=sys.stderr)
            fonts[mode] = TTFont(font_path)
            before = time.perf_counter()
            compact(fonts[mode], mode=str(mode))
            runtimes[mode].append(time.perf_counter() - before)
            font_paths[mode] = (
                font_path.parent
                / "compact"
                / (font_path.stem + f"_{mode}" + font_path.suffix)
            )
            font_paths[mode].parent.mkdir(parents=True, exist_ok=True)
            fonts[mode].save(font_paths[mode])
            fonts[mode] = TTFont(font_paths[mode])
            sizes[mode] = len(fonts[mode].getTableData("GPOS")) / 1024

        print(f"    Runtimes:", file=sys.stderr)
        for mode, times in runtimes.items():
            print(
                f"        {mode:10} {' '.join(f'{t:5.2f}' for t in times)}",
                file=sys.stderr,
            )

        # Bonus: measure WOFF2 file sizes.
        print(f"    Measuring WOFF2 sizes", file=sys.stderr)
        size_woff_orig = woff_size(font, font_path) / 1024
        sizes_woff = {
            mode: woff_size(fonts[mode], font_paths[mode]) / 1024 for mode in MODES
        }

        rows.append(
            (
                font_path.name,
                size_orig,
                size_woff_orig,
                *flatten(
                    (
                        sizes[mode],
                        pct(sizes[mode], size_orig),
                        sizes_woff[mode],
                        pct(sizes_woff[mode], size_woff_orig),
                    )
                    for mode in MODES
                ),
            )
        )

    write_csv(rows)


def woff_size(font: TTFont, path: Path) -> int:
    font.flavor = "woff2"
    woff_path = path.with_suffix(".woff2")
    font.save(woff_path)
    return woff_path.stat().st_size


def write_csv(rows: List[Tuple[Any]]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write("\uFEFF")
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(
        [
            "File",
            "Original GPOS Size",
            "Original WOFF2 Size",
            *flatten(
                (
                    f"mode={mode}",
                    f"Change {mode}",
                    f"mode={mode} WOFF2 Size",
                    f"Change {mode} WOFF2 Size",
                )
                for mode in MODES
            ),
        ]
    )
    for row in rows:
        writer.writerow(row)


def pct(new: float, old: float) -> float:
    return -(1 - (new / old))


def flatten(seq_seq: Iterable[Iterable[Any]]) -> List[Any]:
    return [thing for seq in seq_seq for thing in seq]


if __name__ == "__main__":
    main()
