"""Tests for the ``accf`` (Apple Color Compressed Font) table."""

import io
import struct
import unittest

from fontTools.ttLib.tables._a_c_c_f import (
    HEADER_SIZE,
    MAGIC,
    _decode_palette,
    _encode_palette,
    _png_to_rgba,
    _rgba_to_png,
    decode_image_record,
    encode_image_record,
    table__a_c_c_f,
)


# ── minimal synthetic helpers ────────────────────────────────────────────────


def _make_solid_rgba(
    width: int, height: int, r: int, g: int, b: int, a: int = 255
) -> bytes:
    """Return a solid-colour RGBA image (all pixels the same)."""
    pixel = bytes([r, g, b, a])
    return pixel * (width * height)


def _make_fake_font(glyph_names):
    """Return a minimal stub that satisfies the ``ttFont`` interface."""

    class _FakeFont:
        def getGlyphOrder(self):
            return list(glyph_names)

    return _FakeFont()


def _build_minimal_ccf(
    pixel_sizes=(40,),
    glyphs_per_tier=2,
    image_size=4,
    solid_rgba=(0xFE, 0xFE, 0x00, 0xFF),
):
    """Build a minimal but structurally valid CCF binary in-memory."""
    num_tiers = len(pixel_sizes)
    images_per_tier = glyphs_per_tier
    num_stored = num_tiers * images_per_tier

    # Encode images
    rgba = _make_solid_rgba(image_size, image_size, *solid_rgba)
    encoded_records = [
        encode_image_record(rgba, image_size, image_size) for _ in range(num_stored)
    ]

    # Glyph offset table
    offsets = []
    cumulative = 0
    for rec in encoded_records:
        offsets.append(cumulative)
        cumulative += len(rec)

    # Build 105332-byte header
    header = bytearray(HEADER_SIZE)

    # master header
    struct.pack_into("<4sIII", header, 0, MAGIC, 2, 1, num_tiers)
    for i, sz in enumerate(pixel_sizes):
        struct.pack_into("<I", header, 16 + 4 * i, sz)

    # resolution class map (bytes 47..207)
    # simple: everything maps to last tier
    for px in range(161):
        best = 0
        for ti, sz in enumerate(pixel_sizes):
            if px <= sz:
                best = ti
                break
        else:
            best = num_tiers - 1
        header[px + 47] = best

    # numStoredGlyphs
    struct.pack_into("<I", header, 208, num_stored)

    # Tier LUTs: glyph i → global image index (tier*images_per_tier + i)
    for tier_idx in range(num_tiers):
        lut_base = 212 + 5000 * tier_idx
        tier_img_start = tier_idx * images_per_tier
        for gid in range(images_per_tier):
            struct.pack_into("<H", header, lut_base + 2 * gid, tier_img_start + gid)
        # remaining entries → 0xFFFF (no image)
        for gid in range(images_per_tier, 2500):
            struct.pack_into("<H", header, lut_base + 2 * gid, 0xFFFF)

    # Glyph offset table
    from fontTools.ttLib.tables._a_c_c_f import _OFF_GLYPH_OFFSET_TABLE

    for i, off in enumerate(offsets):
        struct.pack_into("<I", header, _OFF_GLYPH_OFFSET_TABLE + 4 * i, off)

    return bytes(header) + b"".join(encoded_records)


# ── palette codec ────────────────────────────────────────────────────────────


class PaletteCodecTest(unittest.TestCase):
    def test_roundtrip_single_entry(self):
        colors = [(0xFE, 0x80, 0x10)]  # already quantised to even values
        encoded = _encode_palette(colors)
        decoded = _decode_palette(encoded)
        self.assertEqual(len(decoded), 1)
        self.assertAlmostEqual(decoded[0][0], 0xFE, delta=2)
        self.assertAlmostEqual(decoded[0][1], 0x80, delta=2)
        self.assertAlmostEqual(decoded[0][2], 0x10, delta=2)

    def test_roundtrip_eight_entries(self):
        """8 entries pack exactly into 21 bytes."""
        colors = [(i * 32 & 0xFE, i * 16 & 0xFE, i * 8 & 0xFE) for i in range(8)]
        encoded = _encode_palette(colors)
        self.assertEqual(len(encoded), 21)
        decoded = _decode_palette(encoded)
        self.assertEqual(len(decoded), 8)
        for orig, dec in zip(colors, decoded):
            for o, d in zip(orig, dec):
                self.assertAlmostEqual(o, d, delta=2)

    def test_empty(self):
        self.assertEqual(_decode_palette(b""), [])
        self.assertEqual(_encode_palette([]), b"")

    def test_known_bit_pattern(self):
        """Verify bit layout: entry 0 from bytes b0,b1,b2.

        Apple packs BGR in MSB-first order: B in bits[20:14], G in bits[13:7],
        R in bits[6:0].
        """
        # B=0x7F, G=0x3F, R=0x1F  (7-bit values → ×2 = 0xFE, 0x7E, 0x3E)
        # 21-bit entry = (0x7F << 14) | (0x3F << 7) | 0x1F = 0x1FDF9F
        entry = (0x7F << 14) | (0x3F << 7) | 0x1F
        # Pack into 3 bytes big-endian (only 21 bits needed)
        # 3 bytes = 24 bits; entry occupies bits 3..23 (0=MSB of byte 0)
        packed_24 = entry << 3  # align to 24-bit big-endian
        raw = packed_24.to_bytes(3, "big")
        decoded = _decode_palette(raw)
        self.assertTrue(len(decoded) >= 1)
        r, g, b = decoded[0]
        self.assertAlmostEqual(r, 0x1F * 2, delta=2)  # R from LSBs
        self.assertAlmostEqual(g, 0x3F * 2, delta=2)  # G from mid-bits
        self.assertAlmostEqual(b, 0x7F * 2, delta=2)  # B from MSBs


# ── image codec ──────────────────────────────────────────────────────────────


class ImageCodecTest(unittest.TestCase):
    def _solid_roundtrip(self, width, height, r, g, b, a=255):
        rgba = _make_solid_rgba(width, height, r, g, b, a)
        record = encode_image_record(rgba, width, height)
        decoded = decode_image_record(record)
        self.assertEqual(len(decoded), width * height * 4)
        # Allow ±2 for 7-bit quantisation
        for i in range(width * height):
            off = i * 4
            self.assertAlmostEqual(decoded[off], r & 0xFE, delta=2, msg="R mismatch")
            self.assertAlmostEqual(
                decoded[off + 1], g & 0xFE, delta=2, msg="G mismatch"
            )
            self.assertAlmostEqual(
                decoded[off + 2], b & 0xFE, delta=2, msg="B mismatch"
            )
            self.assertEqual(decoded[off + 3], a, msg="A mismatch")

    def test_solid_red_4x4(self):
        self._solid_roundtrip(4, 4, 0xFE, 0, 0)

    def test_solid_green_8x8(self):
        self._solid_roundtrip(8, 8, 0, 0xFE, 0)

    def test_solid_blue_16x16(self):
        self._solid_roundtrip(16, 16, 0, 0, 0xFE)

    def test_transparent_4x4(self):
        self._solid_roundtrip(4, 4, 0, 0, 0, 0)

    def test_partial_alpha(self):
        self._solid_roundtrip(4, 4, 0xFE, 0x80, 0x20, 128)

    def test_random_image_roundtrip(self):
        """A non-trivial image with multiple colours."""
        import random

        rng = random.Random(42)
        w, h = 10, 10
        rgba = bytes(rng.randint(0, 255) for _ in range(w * h * 4))
        record = encode_image_record(rgba, w, h)
        decoded = decode_image_record(record)
        # colours are quantised to 7-bit; allow delta 2.
        # pixels with alpha == 0 are skipped in encoding (they decode to
        # transparent black by the output-buffer default, so their RGB is
        # undefined).
        for i in range(w * h):
            if rgba[i * 4 + 3] == 0:
                continue
            for ch in range(3):
                orig = rgba[i * 4 + ch] & 0xFE
                got = decoded[i * 4 + ch]
                self.assertAlmostEqual(
                    orig, got, delta=2, msg=f"pixel {i} channel {ch}"
                )
            # alpha is lossless
            self.assertEqual(rgba[i * 4 + 3], decoded[i * 4 + 3])

    def test_header_fields(self):
        rgba = _make_solid_rgba(8, 8, 10, 20, 30)
        record = encode_image_record(rgba, 8, 8)
        w, h = struct.unpack_from("<II", record, 0)
        self.assertEqual(w, 8)
        self.assertEqual(h, 8)
        palette_off = struct.unpack_from("<I", record, 8)[0]
        self.assertEqual(palette_off, 40)


# ── PNG helpers ──────────────────────────────────────────────────────────────


class PNGHelpersTest(unittest.TestCase):
    def test_rgba_png_roundtrip(self):
        rgba_orig = _make_solid_rgba(4, 4, 100, 150, 200, 255)
        png = _rgba_to_png(rgba_orig, 4, 4)
        self.assertTrue(png[:4] == b"\x89PNG")
        rgba_back, w, h = _png_to_rgba(png)
        self.assertEqual(w, 4)
        self.assertEqual(h, 4)
        self.assertEqual(rgba_orig, rgba_back)


# ── table decompile/compile ───────────────────────────────────────────────────


class TableTest(unittest.TestCase):
    def _make_table(self, pixel_sizes=(40,), glyph_names=None, glyphs_per_tier=2):
        if glyph_names is None:
            glyph_names = [f"glyph{i:03d}" for i in range(glyphs_per_tier)]
        ccf = _build_minimal_ccf(
            pixel_sizes=pixel_sizes,
            glyphs_per_tier=glyphs_per_tier,
            image_size=4,
        )
        tt = _make_fake_font(glyph_names)
        tbl = table__a_c_c_f(tag="accf")
        tbl.decompile(ccf, tt)
        return tbl, tt

    def test_decompile_strikes(self):
        tbl, _ = self._make_table(pixel_sizes=(40, 64))
        self.assertEqual(sorted(tbl.strikes.keys()), [40, 64])

    def test_decompile_glyph_count(self):
        tbl, _ = self._make_table(pixel_sizes=(40,), glyphs_per_tier=2)
        self.assertEqual(len(tbl.strikes[40].glyphs), 2)

    def test_decompile_glyph_names(self):
        names = ["alpha", "beta"]
        tbl, _ = self._make_table(glyph_names=names)
        self.assertIn("alpha", tbl.strikes[40].glyphs)
        self.assertIn("beta", tbl.strikes[40].glyphs)

    def test_glyph_image_data_is_png(self):
        tbl, _ = self._make_table()
        g = next(iter(tbl.strikes[40].glyphs.values()))
        self.assertIsNotNone(g.imageData)
        self.assertTrue(g.imageData[:4] == b"\x89PNG")

    def test_magic_validation(self):
        ccf = _build_minimal_ccf()
        # Corrupt magic
        bad = b"XXXX" + ccf[4:]
        tt = _make_fake_font(["g0", "g1"])
        tbl = table__a_c_c_f(tag="accf")
        with self.assertRaises(ValueError):
            tbl.decompile(bad, tt)

    def test_too_short_raises(self):
        tbl = table__a_c_c_f(tag="accf")
        with self.assertRaises(ValueError):
            tbl.decompile(b"\x00" * 100, _make_fake_font([]))

    def test_compile_roundtrip(self):
        """decompile → compile should produce a decodable CCF."""
        names = [f"g{i}" for i in range(3)]
        tbl, tt = self._make_table(glyph_names=names)

        recompiled = tbl.compile(tt)
        self.assertTrue(recompiled[:4] == MAGIC)
        self.assertGreater(len(recompiled), HEADER_SIZE)

        tbl2 = table__a_c_c_f(tag="accf")
        tbl2.decompile(recompiled, tt)
        self.assertEqual(sorted(tbl2.strikes.keys()), sorted(tbl.strikes.keys()))

    def test_toxml_fromxml_roundtrip(self):
        from fontTools.misc.xmlWriter import XMLWriter

        names = ["g0", "g1"]
        tbl, tt = self._make_table(glyph_names=names)

        # Export
        buf = io.StringIO()
        w = XMLWriter(buf)
        tbl.toXML(w, tt)
        xml_str = buf.getvalue()
        self.assertIn("<strike", xml_str)
        self.assertIn("<glyph", xml_str)
        self.assertIn('name="g0"', xml_str)

        # Re-import (strip XMLWriter declaration before parsing)
        from xml.etree import ElementTree as ET

        if xml_str.startswith("<?xml"):
            xml_str = xml_str[xml_str.index("?>") + 2 :].lstrip()
        root = ET.fromstring(f"<root>{xml_str}</root>")
        tbl2 = table__a_c_c_f(tag="accf")
        for child in root:
            tag = child.tag
            attrs = child.attrib

            def _to_content(elem):
                content = []
                if elem.text and elem.text.strip():
                    content.append(elem.text.strip())
                for sub in elem:
                    sub_content = _to_content(sub)
                    content.append((sub.tag, sub.attrib, sub_content))
                    if sub.tail and sub.tail.strip():
                        content.append(sub.tail.strip())
                return content

            content = _to_content(child)
            tbl2.fromXML(tag, attrs, content, tt)

        self.assertIn(40, tbl2.strikes)
        self.assertIn("g0", tbl2.strikes[40].glyphs)


if __name__ == "__main__":
    unittest.main()
