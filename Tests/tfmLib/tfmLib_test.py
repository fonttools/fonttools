import glob
import os

import pytest

from fontTools import tfmLib

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.parametrize("path", glob.glob(f"{DATA_DIR}/cm*.tfm"))
def test_read(path):
    tfm = tfmLib.TFM(path)
    assert tfm.designsize == 10.0
    assert tfm.fontdimens
    assert len(tfm.fontdimens) >= 7
    assert tfm.extraheader == {}
    assert tfm.right_boundary_char is None
    assert tfm.left_boundary_char is None
    assert len(tfm.chars) == 128


def test_read_boundary_char():
    path = os.path.join(DATA_DIR, "dummy-space.tfm")
    tfm = tfmLib.TFM(path)
    assert tfm.right_boundary_char == 1
    assert tfm.left_boundary_char == 256


def test_read_fontdimens_vanilla():
    path = os.path.join(DATA_DIR, "cmr10.tfm")
    tfm = tfmLib.TFM(path)
    assert tfm.fontdimens == {
        "SLANT": 0.0,
        "SPACE": 0.33333396911621094,
        "STRETCH": 0.16666698455810547,
        "SHRINK": 0.11111164093017578,
        "XHEIGHT": 0.4305553436279297,
        "QUAD": 1.0000028610229492,
        "EXTRASPACE": 0.11111164093017578,
    }


def test_read_fontdimens_mathex():
    path = os.path.join(DATA_DIR, "cmex10.tfm")
    tfm = tfmLib.TFM(path)
    assert tfm.fontdimens == {
        "SLANT": 0.0,
        "SPACE": 0.0,
        "STRETCH": 0.0,
        "SHRINK": 0.0,
        "XHEIGHT": 0.4305553436279297,
        "QUAD": 1.0000028610229492,
        "EXTRASPACE": 0.0,
        "DEFAULTRULETHICKNESS": 0.03999900817871094,
        "BIGOPSPACING1": 0.11111164093017578,
        "BIGOPSPACING2": 0.16666698455810547,
        "BIGOPSPACING3": 0.19999980926513672,
        "BIGOPSPACING4": 0.6000003814697266,
        "BIGOPSPACING5": 0.10000038146972656,
    }


def test_read_fontdimens_mathsy():
    path = os.path.join(DATA_DIR, "cmsy10.tfm")
    tfm = tfmLib.TFM(path)
    assert tfm.fontdimens == {
        "SLANT": 0.25,
        "SPACE": 0.0,
        "STRETCH": 0.0,
        "SHRINK": 0.0,
        "XHEIGHT": 0.4305553436279297,
        "QUAD": 1.0000028610229492,
        "EXTRASPACE": 0.0,
        "NUM1": 0.6765079498291016,
        "NUM2": 0.39373207092285156,
        "NUM3": 0.44373130798339844,
        "DENOM1": 0.6859512329101562,
        "DENOM2": 0.34484100341796875,
        "SUP1": 0.41289234161376953,
        "SUP2": 0.36289215087890625,
        "SUP3": 0.28888893127441406,
        "SUB1": 0.14999961853027344,
        "SUB2": 0.24721717834472656,
        "SUBDROP": 0.05000019073486328,
        "SUPDROP": 0.3861083984375,
        "DELIM1": 2.3899993896484375,
        "DELIM2": 1.010000228881836,
        "AXISHEIGHT": 0.25,
    }
