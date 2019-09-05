import os
import tempfile

from fontTools.ttLib import TTFont

from fdiff.utils import get_file_modtime
from fdiff.thirdparty.fdifflib import unified_diff


def u_diff(filepath_a, filepath_b, context_lines=3):
    tt_left = TTFont(filepath_a)
    tt_right = TTFont(filepath_b)

    fromdate = get_file_modtime(filepath_a)
    todate = get_file_modtime(filepath_b)

    with tempfile.TemporaryDirectory() as tmpdirname:
        tt_left.saveXML(os.path.join(tmpdirname, "left.ttx"))
        tt_right.saveXML(os.path.join(tmpdirname, "right.ttx"))

        with open(os.path.join(tmpdirname, "left.ttx")) as ff:
            fromlines = ff.readlines()
        with open(os.path.join(tmpdirname, "right.ttx")) as tf:
            tolines = tf.readlines()

        return unified_diff(
            fromlines,
            tolines,
            filepath_a,
            filepath_b,
            fromdate,
            todate,
            n=context_lines,
        )
