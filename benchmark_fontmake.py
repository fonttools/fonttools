#!/usr/bin/env python3
"""Benchmark end-to-end fontmake compilation.

Measures wall-clock time for fontmake to compile a font source into a
variable font. Useful for comparing different fonttools builds, Python
versions, Cython vs pure-Python, etc.

Outputs JSON for easy comparison between builds.

Usage:
    python benchmark_fontmake.py Font.glyphs
    python benchmark_fontmake.py Font.designspace
    python benchmark_fontmake.py Font.glyphs -o variable --rounds 5
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time


def check_compiled_status():
    """Report which fonttools Cython modules are compiled vs pure Python."""
    modules = {}
    from fontTools.cu2qu import cu2qu
    modules["cu2qu"] = getattr(cu2qu, "COMPILED", False)
    from fontTools.qu2cu import qu2cu
    modules["qu2cu"] = getattr(qu2cu, "COMPILED", False)
    from fontTools.misc import bezierTools
    modules["bezierTools"] = getattr(bezierTools, "COMPILED", False)
    from fontTools.pens import momentsPen
    modules["momentsPen"] = getattr(momentsPen, "COMPILED", False)
    from fontTools.varLib import iup
    modules["iup"] = getattr(iup, "COMPILED", False)
    try:
        from fontTools.feaLib import lexer as _lexer
        _dir = os.path.dirname(_lexer.__file__)
        modules["lexer"] = any(
            f.startswith("lexer.") and (f.endswith(".so") or f.endswith(".pyd"))
            for f in os.listdir(_dir)
        )
    except Exception:
        modules["lexer"] = False
    return modules


def bench_fontmake(font_source, output_format, warmup=1, rounds=3):
    """Benchmark fontmake compilation.

    Uses subprocess to call fontmake, ensuring the same Python (and therefore
    the same fonttools with its Cython modules) is used. Subprocess overhead
    is negligible relative to the multi-second compilation.
    """
    tmpdir = tempfile.mkdtemp(prefix="fontmake-bench-")
    font_source = os.path.abspath(font_source)
    name = f"fontmake.{output_format}"

    def run():
        for f in os.listdir(tmpdir):
            fp = os.path.join(tmpdir, f)
            if os.path.isfile(fp):
                os.remove(fp)
            elif os.path.isdir(fp):
                shutil.rmtree(fp)
        result = subprocess.run(
            [sys.executable, "-m", "fontmake",
             font_source,
             "-o", output_format,
             "--output-dir", tmpdir],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"fontmake exited {result.returncode}:\n{result.stderr[-500:]}"
            )

    print(f"  {name} (warmup)...", file=sys.stderr, flush=True)
    for _ in range(warmup):
        run()

    times = []
    for i in range(rounds):
        print(f"  {name} (round {i+1}/{rounds})...", file=sys.stderr,
              end=" ", flush=True)
        t0 = time.perf_counter()
        run()
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        print(f"{elapsed:.2f}s", file=sys.stderr)

    shutil.rmtree(tmpdir, ignore_errors=True)

    best = min(times)
    median = sorted(times)[len(times) // 2]
    mean = sum(times) / len(times)

    return {
        "name": name,
        "font_source": os.path.basename(font_source),
        "output_format": output_format,
        "best_us": best * 1e6,
        "median_us": median * 1e6,
        "mean_us": mean * 1e6,
        "stdev_us": (sum((t - mean)**2 for t in times) / len(times))**0.5 * 1e6,
        "number": 1,
        "rounds": rounds,
        "all_us": [t * 1e6 for t in times],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark end-to-end fontmake compilation")
    parser.add_argument(
        "font_source",
        help="Path to font source (.glyphs, .designspace, .ufo)")
    parser.add_argument(
        "-o", "--output-format", default="variable",
        help="fontmake output format (default: variable)")
    parser.add_argument(
        "--rounds", type=int, default=3,
        help="Number of timed rounds (default: 3)")
    parser.add_argument(
        "--warmup", type=int, default=1,
        help="Number of warmup runs (default: 1)")
    args = parser.parse_args()

    if not os.path.exists(args.font_source):
        print(f"ERROR: Font source not found: {args.font_source}",
              file=sys.stderr)
        sys.exit(1)

    compiled = check_compiled_status()
    print(f"Python {sys.version}", file=sys.stderr)
    print(f"Compiled modules: {compiled}", file=sys.stderr)
    print(f"Font: {args.font_source}", file=sys.stderr)
    print(f"Output: {args.output_format}", file=sys.stderr)

    results = {
        "python_version": sys.version,
        "compiled": compiled,
        "benchmarks": {},
    }

    name = f"fontmake.{args.output_format}"
    try:
        r = bench_fontmake(args.font_source, args.output_format,
                           warmup=args.warmup, rounds=args.rounds)
        results["benchmarks"][name] = r
    except Exception as e:
        print(f"  {name} FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        results["benchmarks"][name] = {"error": str(e)}

    json.dump(results, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
