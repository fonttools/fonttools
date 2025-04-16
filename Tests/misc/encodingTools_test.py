import unittest
from fontTools.misc.encodingTools import getEncoding


class EncodingTest(unittest.TestCase):
    def test_encoding_unicode(self):
        self.assertEqual(
            getEncoding(3, 0, None), "utf_16_be"
        )  # MS Symbol is Unicode as well
        self.assertEqual(getEncoding(3, 1, None), "utf_16_be")
        self.assertEqual(getEncoding(3, 10, None), "utf_16_be")
        self.assertEqual(getEncoding(0, 3, None), "utf_16_be")

    def test_encoding_macroman_misc(self):
        self.assertEqual(getEncoding(1, 0, 17), "mac_turkish")
        self.assertEqual(getEncoding(1, 0, 37), "mac_romanian")
        self.assertEqual(getEncoding(1, 0, 45), "mac_roman")

    def test_extended_mac_encodings(self):
        encoding = getEncoding(1, 1, 0)  # Mac Japanese
        decoded = b"\xfe".decode(encoding)
        self.assertEqual(decoded, chr(0x2122))

    def test_extended_unknown(self):
        self.assertEqual(getEncoding(10, 11, 12), None)
        self.assertEqual(getEncoding(10, 11, 12, "ascii"), "ascii")
        self.assertEqual(getEncoding(10, 11, 12, default="ascii"), "ascii")


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
