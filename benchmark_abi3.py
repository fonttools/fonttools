#!/usr/bin/env python3
"""Benchmark fonttools Cython extensions: abi3 vs regular wheels.

Exercises all 6 Cython-compiled modules with realistic workloads.
Outputs JSON for easy comparison between builds.
"""

import json
import os
import random
import sys
import time

random.seed(42)  # reproducible


def check_compiled_status():
    """Report which modules are compiled vs pure Python."""
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
    # lexer doesn't have COMPILED attribute, check if .so/.pyd exists in its directory
    try:
        from fontTools.feaLib import lexer as _lexer
        import os
        _dir = os.path.dirname(_lexer.__file__)
        modules["lexer"] = any(
            f.startswith("lexer.") and (f.endswith(".so") or f.endswith(".pyd"))
            for f in os.listdir(_dir)
        )
    except Exception:
        modules["lexer"] = False
    return modules


def bench(name, func, warmup=3, rounds=10, min_time=0.1):
    """Benchmark a function with warmup and multiple rounds.

    Uses wall-clock timing with process_time for CPU measurement.
    Returns the minimum time across rounds (standard practice for benchmarking).
    Each round auto-calibrates iterations to reach min_time.
    """
    # warmup
    for _ in range(warmup):
        func()

    # auto-calibrate number of iterations per round
    number = 1
    while True:
        t0 = time.perf_counter()
        for _ in range(number):
            func()
        elapsed = time.perf_counter() - t0
        if elapsed >= min_time:
            break
        number = max(number + 1, int(number * min_time / max(elapsed, 1e-9) * 1.2))

    # actual measurement
    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        for _ in range(number):
            func()
        elapsed = time.perf_counter() - t0
        times.append(elapsed / number)

    best = min(times)
    median = sorted(times)[len(times) // 2]
    mean = sum(times) / len(times)

    return {
        "name": name,
        "best_us": best * 1e6,
        "median_us": median * 1e6,
        "mean_us": mean * 1e6,
        "stdev_us": (sum((t - mean)**2 for t in times) / len(times))**0.5 * 1e6,
        "number": number,
        "rounds": rounds,
        "all_us": [t * 1e6 for t in times],
    }


# ── cu2qu ──────────────────────────────────────────────────────

def generate_cubic():
    return [
        tuple(float(random.randint(0, 2048)) for _ in range(2))
        for _ in range(4)
    ]

CUBICS = [generate_cubic() for _ in range(100)]
MAX_ERR = 0.5


def bench_cu2qu_single():
    from fontTools.cu2qu.cu2qu import curve_to_quadratic
    for c in CUBICS:
        curve_to_quadratic(c, MAX_ERR)


def bench_cu2qu_batch():
    from fontTools.cu2qu.cu2qu import curves_to_quadratic
    curves_to_quadratic(CUBICS, [MAX_ERR] * len(CUBICS))


# ── qu2cu ──────────────────────────────────────────────────────

def _generate_connected_quadratics(n_splines=20):
    """Generate connected quadratic splines for qu2cu benchmark."""
    from fontTools.cu2qu.cu2qu import curve_to_quadratic
    # Generate a connected chain of cubic curves, then convert to quadratic
    quads = []
    # Start point
    last_pt = (float(random.randint(100, 1900)), float(random.randint(100, 1900)))
    for _ in range(n_splines):
        # Generate a cubic starting from last point
        p0 = last_pt
        p1 = (float(random.randint(0, 2048)), float(random.randint(0, 2048)))
        p2 = (float(random.randint(0, 2048)), float(random.randint(0, 2048)))
        p3 = (float(random.randint(0, 2048)), float(random.randint(0, 2048)))
        cubic = [p0, p1, p2, p3]
        quad = curve_to_quadratic(cubic, MAX_ERR)
        quads.append(quad)
        last_pt = p3
    return quads

QUADS = _generate_connected_quadratics(30)


def bench_qu2cu():
    from fontTools.qu2cu.qu2cu import quadratic_to_curves
    quadratic_to_curves(QUADS, MAX_ERR)


# ── bezierTools ────────────────────────────────────────────────

def bench_split_cubic():
    from fontTools.misc.bezierTools import splitCubicAtT
    pts = ((100, 200), (200, 400), (400, 300), (500, 100))
    for _ in range(200):
        splitCubicAtT(*pts, 0.25, 0.5, 0.75)


def bench_arc_length():
    from fontTools.misc.bezierTools import calcCubicArcLength
    for c in CUBICS[:50]:
        calcCubicArcLength(*c)


def bench_approx_arc_length():
    from fontTools.misc.bezierTools import approximateCubicArcLengthC
    curves_c = [[complex(*pt) for pt in c] for c in CUBICS[:50]]
    for c in curves_c:
        approximateCubicArcLengthC(*c)


def bench_solve_cubic():
    from fontTools.misc.bezierTools import solveCubic
    cases = [
        (1, -6, 11, -6),
        (1, 0, -1, 0),
        (2, 3, -11, -6),
        (1, -3, 3, -1),
        (1, 0, 0, -8),
    ]
    for _ in range(200):
        for a, b, c, d in cases:
            solveCubic(a, b, c, d)


# ── momentsPen ─────────────────────────────────────────────────

def bench_moments_pen():
    from fontTools.pens.momentsPen import MomentsPen
    for _ in range(100):
        pen = MomentsPen(glyphset=None)
        pen.moveTo((100, 0))
        pen.lineTo((400, 0))
        pen.curveTo((500, 100), (500, 300), (400, 400))
        pen.lineTo((100, 400))
        pen.curveTo((0, 300), (0, 100), (100, 0))
        pen.closePath()
        _ = pen.area
        _ = pen.momentX
        _ = pen.momentXX


# ── iup ────────────────────────────────────────────────────────

def _generate_iup_data(n_points=80):
    """Generate realistic IUP data (glyph contour with deltas)."""
    coords = [(float(random.randint(0, 1000)), float(random.randint(0, 1000)))
              for _ in range(n_points)]
    deltas = [(float(random.randint(-100, 100)), float(random.randint(-100, 100)))
              for _ in range(n_points)]
    return coords, deltas

IUP_COORDS, IUP_DELTAS = _generate_iup_data(80)


def bench_iup():
    from fontTools.varLib.iup import iup_contour_optimize
    for _ in range(20):
        iup_contour_optimize(IUP_DELTAS, IUP_COORDS, tolerance=0.5)


# ── lexer ──────────────────────────────────────────────────────

def _generate_fea_text():
    lines = []
    for i in range(100):
        lines.append(f"feature liga {{")
        lines.append(f"  lookup liga_{i} {{")
        lines.append(f"    sub f i by fi;")
        lines.append(f"    sub f l by fl;")
        lines.append(f"    sub f f i by ffi;")
        lines.append(f"  }} liga_{i};")
        lines.append(f"}} liga;")
    return "\n".join(lines)

FEA_TEXT = _generate_fea_text()


def bench_lexer():
    from fontTools.feaLib.lexer import Lexer
    for _ in range(10):
        lexer = Lexer(FEA_TEXT, "<benchmark>")
        for token in lexer:
            pass


# ── Pure Python control (no Cython at all) ─────────────────────

def bench_pure_python_control():
    """Pure Python computation as a control — should be identical in both builds."""
    total = 0.0
    for i in range(10000):
        total += (i * 0.001) ** 2 + (i * 0.002) ** 0.5
    return total


# ── Main ───────────────────────────────────────────────────────

BENCHMARKS = [
    ("cu2qu.single",       bench_cu2qu_single),
    ("cu2qu.batch",        bench_cu2qu_batch),
    ("qu2cu",              bench_qu2cu),
    ("bezier.splitCubic",  bench_split_cubic),
    ("bezier.arcLength",   bench_arc_length),
    ("bezier.approxArcC",  bench_approx_arc_length),
    ("bezier.solveCubic",  bench_solve_cubic),
    ("moments.pen",        bench_moments_pen),
    ("iup.contourOpt",     bench_iup),
    ("lexer",              bench_lexer),
    ("pure_python (ctrl)", bench_pure_python_control),
]


def main():
    compiled = check_compiled_status()
    print(f"Python {sys.version}", file=sys.stderr)
    print(f"Compiled modules: {compiled}", file=sys.stderr)

    if not any(compiled.values()):
        print("WARNING: No Cython modules compiled! Pure Python only.", file=sys.stderr)

    results = {
        "python_version": sys.version,
        "compiled": compiled,
        "benchmarks": {},
    }

    for name, func in BENCHMARKS:
        print(f"  {name}...", file=sys.stderr, end=" ", flush=True)
        try:
            r = bench(name, func)
            results["benchmarks"][name] = r
            cv = r["stdev_us"] / r["mean_us"] * 100 if r["mean_us"] > 0 else 0
            print(f"best={r['best_us']:.1f}us median={r['median_us']:.1f}us "
                  f"(CV={cv:.1f}%, {r['number']}x{r['rounds']})", file=sys.stderr)
        except Exception as e:
            print(f"FAILED: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            results["benchmarks"][name] = {"error": str(e)}

    json.dump(results, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
