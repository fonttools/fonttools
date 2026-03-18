import unittest

from fontTools.ttLib import getTableClass


class Test_b_g_c_l(unittest.TestCase):
    """Unit tests for the `bgcl` table implementation."""

    def test_compile_decompile_roundtrip(self):
        cls = getTableClass("bgcl")

        sample = {
            "colors": [[255, 0, 0, 1], [0, 255, 0, 1]],
            "emojicolors": [[[0], [1], []]],
            "indexmap": {"10": 0},
            "version": 1,
        }

        t1 = cls("bgcl")
        t1.json = sample
        data = t1.compile(None)

        t2 = cls("bgcl")
        t2.decompile(data, None)

        self.assertEqual(getattr(t2, "json", None), sample)
