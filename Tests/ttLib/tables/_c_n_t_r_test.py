import io
import json
import unittest

from fontTools.ttLib import getTableClass
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.misc.xmlReader import XMLReader


def _cls():
    return getTableClass("cntr")


def _make_font(glyph_order):
    """Return a minimal TTFont-like object with a glyph order."""

    class FakeFont:
        def getGlyphOrder(self):
            return glyph_order

    return FakeFont()


# Minimal payload that covers: int zero offset, float offset, glyph-ID fallback.
_SAMPLE_JSON = {
    "profiles": {
        # glyph 0  – zero dy stored as int 0
        "0": [[12, 1, 148, 158], [0.07873167406656933, 0]],
        # glyph 1  – both offsets are non-zero floats
        "1": [[1, 6, 154, 154], [-0.006493506493506494, 0.006493506493506494]],
    },
    "size": [160, 160],
    "version": 1,
}

_GLYPH_ORDER = ["uni1F600", "uni1F601"]


class Test_c_n_t_r(unittest.TestCase):
    """Unit tests for the ``cntr`` table implementation."""

    # ------------------------------------------------------------------
    # compile / decompile
    # ------------------------------------------------------------------

    def test_compile_decompile_roundtrip_no_font(self):
        """Round-trip using raw glyph-ID string keys (ttFont=None)."""
        cls = _cls()
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t = cls("cntr")
        t.decompile(raw, None)

        self.assertEqual(t.version, 1)
        self.assertEqual(t.size, [160, 160])
        # With no font the keys remain as glyph-ID strings.
        self.assertIn("0", t.profiles)
        self.assertIn("1", t.profiles)

        data = t.compile(None)
        self.assertEqual(json.loads(data), _SAMPLE_JSON)

    def test_compile_decompile_roundtrip_with_font(self):
        """Round-trip resolves glyph IDs to glyph names via the font."""
        cls = _cls()
        font = _make_font(_GLYPH_ORDER)
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t = cls("cntr")
        t.decompile(raw, font)

        self.assertEqual(t.version, 1)
        self.assertEqual(t.size, [160, 160])
        self.assertIn("uni1F600", t.profiles)
        self.assertIn("uni1F601", t.profiles)
        self.assertEqual(t.profiles["uni1F600"]["bbox"], [12, 1, 148, 158])
        self.assertEqual(t.profiles["uni1F600"]["offset"], [0.07873167406656933, 0])

        data = t.compile(font)
        self.assertEqual(json.loads(data), _SAMPLE_JSON)

    def test_compile_bit_exact(self):
        """compile() output must be byte-for-byte identical to the original."""
        cls = _cls()
        font = _make_font(_GLYPH_ORDER)
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t = cls("cntr")
        t.decompile(raw, font)

        self.assertEqual(t.compile(font), raw)

    def test_integer_zero_offset_preserved(self):
        """Integer 0 in offset must not become float 0.0 on recompile."""
        cls = _cls()
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t = cls("cntr")
        t.decompile(raw, None)

        data = t.compile(None)
        # "0]" must appear (integer zero), not "0.0]"
        self.assertIn(b",0]", data)
        self.assertNotIn(b",0.0]", data)

    def test_glyph_id_fallback_when_out_of_range(self):
        """If glyph ID exceeds glyph order length, key stays as ID string."""
        cls = _cls()
        payload = {
            "profiles": {"999": [[0, 0, 160, 160], [0.0, 0.0]]},
            "size": [160, 160],
            "version": 1,
        }
        raw = json.dumps(payload, separators=(",", ":")).encode()
        font = _make_font(["glyph0"])  # order too short

        t = cls("cntr")
        t.decompile(raw, font)

        self.assertIn("999", t.profiles)

    def test_defaults(self):
        """Newly created table has sensible defaults."""
        t = _cls()("cntr")
        self.assertEqual(t.version, 1)
        self.assertEqual(t.size, [160, 160])
        self.assertEqual(t.profiles, {})

    # ------------------------------------------------------------------
    # toXML / fromXML
    # ------------------------------------------------------------------

    def _roundtrip_xml(self, font):
        cls = _cls()
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t1 = cls("cntr")
        t1.decompile(raw, font)

        buf = io.BytesIO()
        writer = XMLWriter(buf)
        writer.begintag("ttFont", ttLibVersion="4.62")
        writer.newline()
        writer.begintag("cntr")
        writer.newline()
        t1.toXML(writer, font)
        writer.endtag("cntr")
        writer.newline()
        writer.endtag("ttFont")
        writer.newline()
        writer.close()

        # Build a fake TTFont that XMLReader can populate.
        from fontTools.ttLib import TTFont

        tt = TTFont()
        tt.setGlyphOrder(font.getGlyphOrder() if font is not None else [])
        reader = XMLReader(io.BytesIO(buf.getvalue()), tt)
        reader.read()
        return tt["cntr"]

    def test_toxml_fromxml_roundtrip_with_font(self):
        font = _make_font(_GLYPH_ORDER)
        t2 = self._roundtrip_xml(font)

        self.assertEqual(t2.version, 1)
        self.assertEqual(t2.size, [160, 160])
        self.assertIn("uni1F600", t2.profiles)
        self.assertIn("uni1F601", t2.profiles)
        self.assertEqual(t2.profiles["uni1F600"]["bbox"], [12, 1, 148, 158])

    def test_toxml_fromxml_roundtrip_no_font(self):
        t2 = self._roundtrip_xml(None)

        self.assertEqual(t2.version, 1)
        self.assertEqual(t2.size, [160, 160])

    def test_toxml_fromxml_compile_bit_exact(self):
        """A full toXML→fromXML→compile cycle must reproduce the original bytes."""
        font = _make_font(_GLYPH_ORDER)
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t2 = self._roundtrip_xml(font)

        from fontTools.ttLib import TTFont

        tt = TTFont()
        tt.setGlyphOrder(_GLYPH_ORDER)
        self.assertEqual(t2.compile(tt), raw)

    def test_toxml_uses_glyph_name_attribute(self):
        """<profile> elements should carry a 'name' attribute when font is known."""
        font = _make_font(_GLYPH_ORDER)
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t = _cls()("cntr")
        t.decompile(raw, font)

        buf = io.BytesIO()
        writer = XMLWriter(buf)
        t.toXML(writer, font)
        writer.close()
        xml = buf.getvalue().decode()

        self.assertIn('name="uni1F600"', xml)
        self.assertNotIn("glyphID", xml)

    def test_toxml_uses_glyphid_fallback(self):
        """<profile> elements fall back to 'glyphID' when font is unavailable."""
        raw = json.dumps(_SAMPLE_JSON, separators=(",", ":")).encode()

        t = _cls()("cntr")
        t.decompile(raw, None)  # keys stay as "0", "1"

        buf = io.BytesIO()
        writer = XMLWriter(buf)
        t.toXML(writer, None)
        writer.close()
        xml = buf.getvalue().decode()

        self.assertIn("glyphID=", xml)


if __name__ == "__main__":
    unittest.main()
