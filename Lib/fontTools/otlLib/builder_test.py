from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.otlLib import builder
import unittest


class BuilderTest(unittest.TestCase):
    def test_getLigatureKey(self):
        components = lambda s: [tuple(word) for word in s.split()]
        c = components("fi fl ff ffi fff")
        c.sort(key=builder.getLigatureKey)
        self.assertEquals(c, components("fff ffi ff fi fl"))


if __name__ == "__main__":
    unittest.main()
