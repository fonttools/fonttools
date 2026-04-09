"""Tests that every table module is registered in all required locations.

Imports the check functions from MetaTools/check_table_coverage.py directly
so no subprocess or PYTHONPATH juggling is needed.
"""

import sys
import os

import pytest

# MetaTools/ is not a package; add it to sys.path so we can import from it.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "MetaTools"))

from check_table_coverage import (  # noqa: E402
    check_init_py,
    check_ttfont_py,
    check_ttx_rst,
    check_rst_docs,
    check_tables_rst,
    get_table_modules,
)


@pytest.fixture(scope="module")
def table_modules():
    return get_table_modules()


def _run(check_fn, table_modules):
    errors, warnings = [], []
    check_fn(table_modules, errors, warnings, strict=False)
    return errors


def test_init_py(table_modules):
    errors = _run(check_init_py, table_modules)
    assert not errors, "\n" + "\n".join(errors)


def test_ttx_rst(table_modules):
    errors = _run(check_ttx_rst, table_modules)
    assert not errors, "\n" + "\n".join(errors)


def test_ttfont_py(table_modules):
    errors = _run(check_ttfont_py, table_modules)
    assert not errors, "\n" + "\n".join(errors)


def test_rst_docs(table_modules):
    errors = _run(check_rst_docs, table_modules)
    assert not errors, "\n" + "\n".join(errors)


def test_tables_rst_toctree(table_modules):
    errors = _run(check_tables_rst, table_modules)
    assert not errors, "\n" + "\n".join(errors)
