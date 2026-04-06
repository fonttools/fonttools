#!/usr/bin/env python3
"""Verify that all table modules are registered in every required location.

When a new table module is added (e.g. Lib/fontTools/ttLib/tables/_b_g_c_l.py),
this script checks that the contributor ALSO updated:

  A. Lib/fontTools/ttLib/tables/__init__.py     (auto-generated — run buildTableList.py)
  B. Doc/source/ttx.rst                         (auto-generated — run buildTableList.py)
  C. Lib/fontTools/ttLib/ttFont.py              (TYPE_CHECKING import + @overload stubs)
  D. Doc/source/ttLib/tables/<module>.rst       (per-table automodule stub)
  E. Doc/source/ttLib/tables.rst                (toctree entry)
  F. Tests/ttLib/tables/<module>_test.py        (unit tests — warning only by default)

Checks A & B are satisfied by running:
    PYTHONPATH=Lib python MetaTools/buildTableList.py

Usage:
    PYTHONPATH=Lib python MetaTools/check_table_coverage.py [--strict]

    --strict   Promote all known-gap warnings to errors (useful for auditing debt).

Exit code is 0 only when no errors are found.
"""

import argparse
import glob
import os
import re
import sys

# ---------------------------------------------------------------------------
# Bootstrap: make fontTools importable from Lib/ when running as a script
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, os.path.join(_REPO_ROOT, "Lib"))

from fontTools.ttLib import identifierToTag  # noqa: E402 — after sys.path tweak

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TABLES_DIR = os.path.join(_REPO_ROOT, "Lib", "fontTools", "ttLib", "tables")
INIT_FILE = os.path.join(TABLES_DIR, "__init__.py")
TTX_RST = os.path.join(_REPO_ROOT, "Doc", "source", "ttx.rst")
TTFONT_PY = os.path.join(_REPO_ROOT, "Lib", "fontTools", "ttLib", "ttFont.py")
TABLES_RST = os.path.join(_REPO_ROOT, "Doc", "source", "ttLib", "tables.rst")
TABLE_DOCS_DIR = os.path.join(_REPO_ROOT, "Doc", "source", "ttLib", "tables")
TESTS_DIR = os.path.join(_REPO_ROOT, "Tests", "ttLib", "tables")

# ---------------------------------------------------------------------------
# Modules that are documented in a shared grouping RST rather than having
# their own individual RST file and toctree entry.
# Maps module_name -> grouping_rst (relative to TABLE_DOCS_DIR).
# ---------------------------------------------------------------------------
GROUPED_IN: dict[str, str] = {
    # TSI* VTT tables are all documented together in VTT_related.rst
    "T_S_I__0": "VTT_related.rst",
    "T_S_I__1": "VTT_related.rst",
    "T_S_I__2": "VTT_related.rst",
    "T_S_I__3": "VTT_related.rst",
    "T_S_I__5": "VTT_related.rst",
    "T_S_I_B_": "VTT_related.rst",
    "T_S_I_C_": "VTT_related.rst",
    "T_S_I_D_": "VTT_related.rst",
    "T_S_I_J_": "VTT_related.rst",
    "T_S_I_P_": "VTT_related.rst",
    "T_S_I_S_": "VTT_related.rst",
    "T_S_I_V_": "VTT_related.rst",
}

# ---------------------------------------------------------------------------
# Known pre-existing gaps (maintenance debt).
#
# Keys are the Python module identifier (filename without .py).
# Values are sets of check IDs that are currently failing for that module.
# Entries here become *warnings* instead of *errors* so the CI can be added
# without breaking on existing debt.  Remove an entry once it is fixed.
#
# Check IDs:  init_py | ttx_rst | ttfont_import | ttfont_overload |
#             rst_doc | tables_rst | test_file
# ---------------------------------------------------------------------------
KNOWN_GAPS: dict[str, set[str]] = {
    "B_A_S_E_": {"test_file"},
    "C_B_D_T_": {"test_file"},
    "C_B_L_C_": {"test_file"},
    "C_F_F_": {"test_file"},
    "C_O_L_R_": {"test_file"},
    "C_P_A_L_": {"test_file"},
    "D_S_I_G_": {"test_file"},
    "E_B_D_T_": {"test_file"},
    "E_B_L_C_": {"test_file"},
    "F_F_T_M_": {"test_file"},
    "F__e_a_t": {"test_file"},
    "G_D_E_F_": {"test_file"},
    "G_P_O_S_": {"test_file"},
    "G_S_U_B_": {"test_file"},
    "G_V_A_R_": {"test_file"},
    "G__l_a_t": {"test_file"},
    "G__l_o_c": {"test_file"},
    "H_V_A_R_": {"test_file"},
    "I_F_T_": {"test_file"},
    "I_F_T_X_": {"test_file"},
    "J_S_T_F_": {"test_file"},
    "L_T_S_H_": {"test_file"},
    "M_A_T_H_": {"test_file"},
    "M_V_A_R_": {"test_file"},
    "S_T_A_T_": {"test_file"},
    "S__i_l_f": {"test_file"},
    "S__i_l_l": {"test_file"},
    "T_S_I__2": {"test_file"},
    "T_S_I__3": {"test_file"},
    "T_S_I_B_": {"test_file"},
    "T_S_I_C_": {"test_file"},
    "T_S_I_D_": {"test_file"},
    "T_S_I_J_": {"test_file"},
    "T_S_I_P_": {"test_file"},
    "T_S_I_S_": {"test_file"},
    "T_S_I_V_": {"test_file"},
    "T_T_F_A_": {"test_file"},
    "V_A_R_C_": {"test_file"},
    "V_D_M_X_": {"test_file"},
    "V_O_R_G_": {"test_file"},
    "V_V_A_R_": {"test_file"},
    "_f_e_a_t": {"test_file"},
    "_g_a_s_p": {"test_file"},
    "_h_d_m_x": {"test_file"},
    "_h_e_a_d": {"test_file"},
    "_l_o_c_a": {"test_file"},
    "_m_a_x_p": {"test_file"},
    "_p_r_e_p": {"test_file"},
    "_s_b_i_x": {"test_file"},
}


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def get_table_modules() -> list[tuple[str, str]]:
    """Return sorted list of (module_name, tag_raw) for all table .py files."""
    modules = []
    for filename in glob.glob1(TABLES_DIR, "*.py"):
        name = filename[:-3]
        try:
            tag = identifierToTag(name)  # may contain trailing spaces, e.g. "cvt "
        except Exception:
            continue
        modules.append((name, tag))
    return sorted(modules)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_init_py(
    modules: list[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Check A: every module has 'from . import <module>' in __init__.py."""
    with open(INIT_FILE) as f:
        content = f.read()
    for module, tag in modules:
        tag_stripped = tag.strip()
        if f"    from . import {module}\n" not in content:
            msg = (
                f"[A] tables/__init__.py: 'from . import {module}' is missing "
                f"(tag '{tag_stripped}').\n"
                f"      Fix: run  PYTHONPATH=Lib python MetaTools/buildTableList.py"
            )
            _report(msg, "init_py", module, errors, warnings, strict)


def check_ttx_rst(
    modules: list[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Check B: every table's tag appears in the ttx.rst table list block."""
    with open(TTX_RST) as f:
        doc = f.read()
    begin = ".. begin table list\n"
    end = ".. end table list"
    b = doc.find(begin)
    e = doc.find(end)
    if b < 0 or e < 0:
        errors.append(
            "[B] Doc/source/ttx.rst: '.. begin table list' / '.. end table list' "
            "markers are missing."
        )
        return
    block = doc[b:e]
    for module, tag in modules:
        tag_stripped = tag.strip()
        # Word-boundary search so e.g. "cvt" doesn't match inside another token
        if not re.search(
            r"(?<![A-Za-z0-9/])" + re.escape(tag_stripped) + r"(?![A-Za-z0-9/])", block
        ):
            msg = (
                f"[B] Doc/source/ttx.rst: tag '{tag_stripped}' is absent from the "
                f"table list (module '{module}').\n"
                f"      Fix: run  PYTHONPATH=Lib python MetaTools/buildTableList.py"
            )
            _report(msg, "ttx_rst", module, errors, warnings, strict)


def check_ttfont_py(
    modules: list[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Check C: every module has a TYPE_CHECKING import and @overload stubs in ttFont.py."""
    with open(TTFONT_PY) as f:
        content = f.read()
    for module, tag in modules:
        tag_stripped = tag.strip()
        # TYPE_CHECKING import block indented with 8 spaces
        if f"        {module}," not in content:
            msg = (
                f"[C] ttFont.py: TYPE_CHECKING import missing for '{module}' "
                f"(tag '{tag_stripped}').\n"
                f"      Fix: add '        {module},' to the TYPE_CHECKING import block."
            )
            _report(msg, "ttfont_import", module, errors, warnings, strict)
        # @overload stub — tag_raw (with any trailing space) inside Literal["..."]
        if f'Literal["{tag}"]' not in content:
            msg = (
                f'[C] ttFont.py: @overload stub for Literal["{tag}"] is missing '
                f"(module '{module}').\n"
                f"      Fix: add @overload stubs for __getitem__ and get() "
                f'with Literal["{tag}"].'
            )
            _report(msg, "ttfont_overload", module, errors, warnings, strict)


def check_rst_docs(
    modules: list[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Check D: Doc/source/ttLib/tables/<module>.rst must exist."""
    for module, tag in modules:
        tag_stripped = tag.strip()
        # Modules intentionally documented via a shared grouping RST — skip individual checks
        if module in GROUPED_IN:
            grouping = GROUPED_IN[module]
            grouping_path = os.path.join(TABLE_DOCS_DIR, grouping)
            if not os.path.exists(grouping_path):
                errors.append(
                    f"[D] grouped RST '{grouping}' referenced by '{module}' "
                    f"does not exist at {grouping_path}"
                )
            continue
        rst_path = os.path.join(TABLE_DOCS_DIR, f"{module}.rst")
        if not os.path.exists(rst_path):
            msg = (
                f"[D] Doc/source/ttLib/tables/{module}.rst: file does not exist "
                f"(tag '{tag_stripped}').\n"
                f"      Fix: create the file with an automodule directive, e.g.:\n\n"
                f"        ``{tag_stripped}``: <Short description>\n"
                f"        {'~' * (len(tag_stripped) + 20)}\n\n"
                f"        .. automodule:: fontTools.ttLib.tables.{module}\n"
                f"           :members:\n"
                f"           :undoc-members:"
            )
            _report(msg, "rst_doc", module, errors, warnings, strict)


def check_tables_rst(
    modules: list[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Check E: Doc/source/ttLib/tables.rst must have a toctree entry."""
    with open(TABLES_RST) as f:
        content = f.read()
    for module, tag in modules:
        tag_stripped = tag.strip()
        # Grouped tables appear under the grouping RST; the grouping RST itself
        # must be in the toctree (that is already verified elsewhere).
        if module in GROUPED_IN:
            continue
        if f"   tables/{module}\n" not in content:
            msg = (
                f"[E] Doc/source/ttLib/tables.rst: toctree entry "
                f"'   tables/{module}' is missing (tag '{tag_stripped}').\n"
                f"      Fix: add '   tables/{module}' to the "
                f"'Tables currently supported' toctree (in alphabetical order)."
            )
            _report(msg, "tables_rst", module, errors, warnings, strict)


def check_test_files(
    modules: list[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Check F: Tests/ttLib/tables/<module>_test.py should exist (warning by default)."""
    for module, tag in modules:
        tag_stripped = tag.strip()
        test_path = os.path.join(TESTS_DIR, f"{module}_test.py")
        if not os.path.exists(test_path):
            msg = (
                f"[F] Tests/ttLib/tables/{module}_test.py: no test file "
                f"(tag '{tag_stripped}')."
            )
            if strict:
                _report(msg, "test_file", module, errors, warnings, strict)
            else:
                # Always a warning regardless of KNOWN_GAPS, unless strict
                gaps = KNOWN_GAPS.get(module, set())
                if "test_file" not in gaps:
                    warnings.append(msg)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _report(
    msg: str,
    check_id: str,
    module: str,
    errors: list[str],
    warnings: list[str],
    strict: bool,
) -> None:
    """Route msg to errors or warnings depending on KNOWN_GAPS and strict mode."""
    gaps = KNOWN_GAPS.get(module, set())
    if strict or check_id not in gaps:
        errors.append(msg)
    else:
        warnings.append(f"[known gap] {msg}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat all known-gap warnings as errors (useful for auditing existing debt).",
    )
    args = parser.parse_args()

    modules = get_table_modules()
    errors: list[str] = []
    warnings: list[str] = []

    check_init_py(modules, errors, warnings, args.strict)
    check_ttx_rst(modules, errors, warnings, args.strict)
    check_ttfont_py(modules, errors, warnings, args.strict)
    check_rst_docs(modules, errors, warnings, args.strict)
    check_tables_rst(modules, errors, warnings, args.strict)
    check_test_files(modules, errors, warnings, args.strict)

    if warnings:
        print(f"Warnings ({len(warnings)}) — pre-existing gaps, not blocking CI:")
        for w in warnings:
            print(f"  \u26a0  {w}")
        print()

    if errors:
        print(
            f"ERRORS — {len(errors)} problem(s) found.\n"
            "New table modules must update all required locations.\n"
        )
        for e in errors:
            print(f"  \u2717  {e}")
        print()
        print(
            "Checklist for adding a new table:\n"
            "  1. Create  Lib/fontTools/ttLib/tables/<module>.py\n"
            "  2. Run     PYTHONPATH=Lib python MetaTools/buildTableList.py\n"
            "             (updates __init__.py and Doc/source/ttx.rst automatically)\n"
            "  3. Add TYPE_CHECKING import + @overload stubs  in ttFont.py\n"
            "  4. Create  Doc/source/ttLib/tables/<module>.rst\n"
            "  5. Add toctree entry in Doc/source/ttLib/tables.rst\n"
            "  6. Create  Tests/ttLib/tables/<module>_test.py"
        )
        sys.exit(1)

    print(
        f"OK: {len(modules)} table modules checked — "
        "all required locations are up to date."
    )
    if warnings:
        print(
            f"    ({len(warnings)} known pre-existing gap(s) noted above — "
            "not blocking this check)"
        )


if __name__ == "__main__":
    main()
