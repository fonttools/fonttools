from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.location import FeatureLibLocation
import unittest


class FeatureLibErrorTest(unittest.TestCase):
    def test_str(self):
        err = FeatureLibError("Squeak!", FeatureLibLocation("foo.fea", 23, 42))
        self.assertEqual(str(err), "foo.fea:23:42: Squeak!")

    def test_str_nolocation(self):
        err = FeatureLibError("Squeak!", None)
        self.assertEqual(str(err), "Squeak!")


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
