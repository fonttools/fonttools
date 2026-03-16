#!/usr/bin/env python3
"""Compare abi3 vs regular benchmark results.

Reads JSON result files from /tmp/fonttools-abi3-bench/ (or a custom dir)
and prints a comparison table.

Usage:
    python compare_abi3_results.py
    python compare_abi3_results.py /path/to/results/dir
"""

import json
import glob
import os
import sys

BENCH_DIR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fonttools-abi3-bench"


def load_best(*patterns):
    """Load results from multiple glob patterns, pick the best (minimum) per benchmark."""
    files = []
    for pattern in patterns:
        files.extend(sorted(glob.glob(os.path.join(BENCH_DIR, pattern))))
    if not files:
        return None

    all_results = []
    for f in files:
        with open(f) as fh:
            all_results.append(json.load(fh))

    merged = {
        "python_version": all_results[0]["python_version"],
        "compiled": all_results[0]["compiled"],
        "benchmarks": {},
    }

    for r in all_results:
        for name, data in r["benchmarks"].items():
            if "error" in data:
                if name not in merged["benchmarks"]:
                    merged["benchmarks"][name] = data
                continue
            if name not in merged["benchmarks"] or "error" in merged["benchmarks"][name]:
                merged["benchmarks"][name] = data
            elif data["best_us"] < merged["benchmarks"][name]["best_us"]:
                merged["benchmarks"][name] = data

    return merged


def format_time(us):
    """Format microseconds as human-readable."""
    if us >= 1_000_000:
        return f"{us/1_000_000:.2f}s"
    elif us >= 1_000:
        return f"{us/1_000:.1f}ms"
    else:
        return f"{us:.1f}us"


def print_table(names, header, regular, abi3, use_human_time=False):
    print(header)
    if use_human_time:
        print(f"{'Benchmark':<25} {'Regular':>14} {'ABI3':>14} {'Diff':>10}")
    else:
        print(f"{'Benchmark':<25} {'Regular (us)':>14} {'ABI3 (us)':>14} {'Diff':>10}")
    print('-' * 67)

    diffs = []
    for name in names:
        r = regular["benchmarks"].get(name, {})
        a = abi3["benchmarks"].get(name, {})
        if "error" in r or "error" in a:
            err = r.get("error", a.get("error", "?"))[:30]
            print(f"{name:<25} {'ERR':>14} {'ERR':>14}   {err}")
            continue
        r_us = r["best_us"]
        a_us = a["best_us"]
        diff_pct = (a_us - r_us) / r_us * 100
        diffs.append(diff_pct)
        if use_human_time:
            print(f"{name:<25} {format_time(r_us):>14} {format_time(a_us):>14} {diff_pct:>+9.1f}%")
        else:
            print(f"{name:<25} {r_us:>14.1f} {a_us:>14.1f} {diff_pct:>+9.1f}%")

    if diffs:
        avg = sum(diffs) / len(diffs)
        median = sorted(diffs)[len(diffs) // 2]
        print('-' * 67)
        print(f"{'Average':>25} {'':>14} {'':>14} {avg:>+9.1f}%")
        print(f"{'Median':>25} {'':>14} {'':>14} {median:>+9.1f}%")
    return diffs


def main():
    n_rounds = len(glob.glob(os.path.join(BENCH_DIR, "results-regular-r*.json")))

    regular = load_best("results-regular-r*.json", "e2e-regular-r*.json")
    abi3 = load_best("results-abi3-r*.json", "e2e-abi3-r*.json")

    if not regular or not abi3:
        print("ERROR: Could not load results")
        sys.exit(1)

    print(f"Python: {regular['python_version'].split()[0]}")
    print(f"Rounds: {n_rounds} per variant (alternating), reporting best-of-{n_rounds}")

    # Categorize benchmarks
    micro_benches = []
    e2e_benches = []
    control_benches = []

    for name in regular["benchmarks"]:
        if "control" in name or "ctrl" in name:
            control_benches.append(name)
        elif name.startswith("fontmake."):
            e2e_benches.append(name)
        else:
            micro_benches.append(name)

    print()
    print_table(micro_benches, "── Cython-compiled micro-benchmarks ──", regular, abi3)
    print()
    control_diffs = print_table(
        control_benches, "── Control (pure Python, should be ~0%) ──", regular, abi3)

    if e2e_benches:
        print()
        print_table(
            e2e_benches, "── End-to-end fontmake compilation ──",
            regular, abi3, use_human_time=True)
        for name in e2e_benches:
            r = regular["benchmarks"].get(name, {})
            src = r.get("font_source", "")
            if src:
                print(f"  (font: {src})")
                break

    if control_diffs:
        ctrl_avg = sum(abs(d) for d in control_diffs) / len(control_diffs)
        print()
        print(f"Control variance: +/-{ctrl_avg:.1f}%")
        if ctrl_avg > 5:
            print("WARNING: High control variance — system load may have affected results.")

    print()
    print(f"Raw results: {BENCH_DIR}/results-*.json")


if __name__ == "__main__":
    main()
