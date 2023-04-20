import unittest
import fontTools.encodings.codecs  # Not to be confused with "import codecs"


class ExtendedCodecsTest(unittest.TestCase):
    def test_decode_mac_japanese(self):
        self.assertEqual(
            b"x\xfe\xfdy".decode("x_mac_japanese_ttx"),
            chr(0x78) + chr(0x2122) + chr(0x00A9) + chr(0x79),
        )

    def test_encode_mac_japanese(self):
        self.assertEqual(
            b"x\xfe\xfdy",
            (chr(0x78) + chr(0x2122) + chr(0x00A9) + chr(0x79)).encode(
                "x_mac_japanese_ttx"
            ),
        )

    def test_decode_mac_trad_chinese(self):
        self.assertEqual(b"\x80".decode("x_mac_trad_chinese_ttx"), chr(0x5C))

    def test_decode_mac_romanian(self):
        self.assertEqual(b"x\xfb".decode("mac_romanian"), chr(0x78) + chr(0x02DA))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
