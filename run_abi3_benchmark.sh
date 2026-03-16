#!/bin/bash
# Compare performance: regular Cython wheels vs abi3 wheels
# Builds fonttools from two branches (main, abi3-wheels) and benchmarks both.
# Runs 3 rounds alternating between builds to control for system load variance.
#
# Usage:
#   ./run_abi3_benchmark.sh                              # micro-benchmarks only
#   ./run_abi3_benchmark.sh /path/to/Font.glyphs         # + fontmake e2e
#   ./run_abi3_benchmark.sh /path/to/Font.designspace    # + fontmake e2e
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

FONT_SOURCE="${1:-}"
if [[ -n "$FONT_SOURCE" ]]; then
    FONT_SOURCE="$(cd "$(dirname "$FONT_SOURCE")" && pwd)/$(basename "$FONT_SOURCE")"
    if [[ ! -e "$FONT_SOURCE" ]]; then
        echo "ERROR: Font source not found: $FONT_SOURCE"
        exit 1
    fi
    echo "Font source: $FONT_SOURCE"
fi

BENCH_DIR="/tmp/fonttools-abi3-bench"
rm -rf "$BENCH_DIR"
mkdir -p "$BENCH_DIR"

cleanup() {
    cd "$REPO_DIR"
    git worktree remove --force "$BENCH_DIR/worktree-regular" 2>/dev/null || true
    git worktree remove --force "$BENCH_DIR/worktree-abi3" 2>/dev/null || true
}
trap cleanup EXIT

echo "=== fonttools abi3 vs regular Cython benchmark ==="
echo "Repo: $REPO_DIR"
echo

# Git refs for the two builds
REGULAR_REF="222326ec7"  # pre-abi3: "Bump version: 4.62.1 → 4.62.2.dev0"
ABI3_REF="69f6a9cf3"     # abi3: "Build abi3 wheels for Cython extensions"

# ── Build regular (non-abi3) ──
echo ">>> Building REGULAR (non-abi3) from $(git log --oneline -1 "$REGULAR_REF")..."
VENV_REGULAR="$BENCH_DIR/venv-regular"
uv venv "$VENV_REGULAR" --quiet
PYTHON_REGULAR="$VENV_REGULAR/bin/python"
uv pip install --python "$PYTHON_REGULAR" cython setuptools --quiet

WORK_REGULAR="$BENCH_DIR/worktree-regular"
git worktree add "$WORK_REGULAR" "$REGULAR_REF" --detach

cd "$WORK_REGULAR"
cp "$REPO_DIR/benchmark_abi3.py" "$REPO_DIR/benchmark_fontmake.py" .
if [[ -n "$FONT_SOURCE" ]]; then
    echo "  Installing fontmake (before editable fonttools)..."
    uv pip install --python "$PYTHON_REGULAR" fontmake --quiet
fi
# Install editable fonttools with Cython AFTER fontmake, so the Cython build
# overrides the PyPI fonttools that fontmake pulled in as a dependency.
FONTTOOLS_WITH_CYTHON=1 uv pip install --python "$PYTHON_REGULAR" -e . --no-build-isolation --quiet 2>&1 | tail -3
echo "Regular build done."

# ── Build abi3 from PR branch ──
echo ">>> Building ABI3 from abi3-wheels branch..."
VENV_ABI3="$BENCH_DIR/venv-abi3"
uv venv "$VENV_ABI3" --quiet
PYTHON_ABI3="$VENV_ABI3/bin/python"
uv pip install --python "$PYTHON_ABI3" cython setuptools --quiet

WORK_ABI3="$BENCH_DIR/worktree-abi3"
git worktree add "$WORK_ABI3" "$ABI3_REF" --detach

cd "$WORK_ABI3"
cp "$REPO_DIR/benchmark_abi3.py" "$REPO_DIR/benchmark_fontmake.py" .
if [[ -n "$FONT_SOURCE" ]]; then
    echo "  Installing fontmake (before editable fonttools)..."
    uv pip install --python "$PYTHON_ABI3" fontmake --quiet
fi
FONTTOOLS_WITH_CYTHON=1 uv pip install --python "$PYTHON_ABI3" -e . --no-build-isolation --quiet 2>&1 | tail -3
echo "ABI3 build done."
echo

# ── Verify .so file tags ──
echo ">>> Verifying builds..."
echo "Regular .so files:"
find "$WORK_REGULAR/Lib" -name "*.so" -exec basename {} \; 2>/dev/null | sort
echo "ABI3 .so files:"
find "$WORK_ABI3/Lib" -name "*.so" -exec basename {} \; 2>/dev/null | sort
echo

# ── Run 3 rounds, alternating ──
N_ROUNDS=3
echo ">>> Running $N_ROUNDS rounds (alternating Regular/ABI3)..."
echo

for round in $(seq 1 $N_ROUNDS); do
    echo "--- Round $round/$N_ROUNDS: REGULAR ---"
    cd "$WORK_REGULAR"
    "$PYTHON_REGULAR" benchmark_abi3.py \
        1>"$BENCH_DIR/results-regular-r${round}.json" \
        2>"$BENCH_DIR/log-regular-r${round}.txt"
    cat "$BENCH_DIR/log-regular-r${round}.txt"
    if [[ -n "$FONT_SOURCE" ]]; then
        "$PYTHON_REGULAR" benchmark_fontmake.py "$FONT_SOURCE" \
            1>"$BENCH_DIR/e2e-regular-r${round}.json" \
            2>"$BENCH_DIR/log-e2e-regular-r${round}.txt"
        cat "$BENCH_DIR/log-e2e-regular-r${round}.txt"
    fi
    echo

    echo "--- Round $round/$N_ROUNDS: ABI3 ---"
    cd "$WORK_ABI3"
    "$PYTHON_ABI3" benchmark_abi3.py \
        1>"$BENCH_DIR/results-abi3-r${round}.json" \
        2>"$BENCH_DIR/log-abi3-r${round}.txt"
    cat "$BENCH_DIR/log-abi3-r${round}.txt"
    if [[ -n "$FONT_SOURCE" ]]; then
        "$PYTHON_ABI3" benchmark_fontmake.py "$FONT_SOURCE" \
            1>"$BENCH_DIR/e2e-abi3-r${round}.json" \
            2>"$BENCH_DIR/log-e2e-abi3-r${round}.txt"
        cat "$BENCH_DIR/log-e2e-abi3-r${round}.txt"
    fi
    echo
done

# ── Compare (best-of-N-rounds for each benchmark) ──
echo "=== COMPARISON (best of $N_ROUNDS rounds) ==="
cd "$REPO_DIR"
"$PYTHON_REGULAR" compare_abi3_results.py "$BENCH_DIR"
