from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
import unittest


class FeatureLibErrorTest(unittest.TestCase):
    def test_str(self):
        err = FeatureLibError("Squeak!", ("foo.fea", 23, 42))
        self.assertEqual(str(err), "foo.fea:23:42: Squeak!")

    def test_str_nolocation(self):
        err = FeatureLibError("Squeak!", None)
        self.assertEqual(str(err), "Squeak!")


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
