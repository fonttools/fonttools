from fontTools.ttLib import TTFont
from fontTools.varLib.hvar import add_HVAR
from io import StringIO
import os
import unittest
import pytest


def test_roundtrip():
    CWD = os.path.abspath(os.path.dirname(__file__))
    DATADIR = os.path.join(CWD, "data")
    ttx_path = os.path.join(DATADIR, "MutatorSans_All_Variable.ttx")
    font = TTFont()
    font.importXML(ttx_path)

    HVAR1 = StringIO()
    font.saveXML(HVAR1, tables=["HVAR"])

    del font["HVAR"]
    add_HVAR(font)

    HVAR2 = StringIO()
    font.saveXML(HVAR2, tables=["HVAR"])

    assert HVAR1.getvalue() == HVAR2.getvalue()
