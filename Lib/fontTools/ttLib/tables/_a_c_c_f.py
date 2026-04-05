"""Apple Color Compressed Font (``accf``) table implementation.

The ``accf`` table (tag ``accf``) is a private Apple table used in certain
iOS / macOS colour-emoji fonts (seen in iOS 8.3 up to iOS 9.3).  It stores
glyph images using a proprietary run-length + palette-indexed compression
scheme that is significantly more compact than the ``sbix`` PNG approach.

Two wire formats exist:

* **Version 1** (iOS 8.x) — magic ``b'\\x40\\x30\\x20\\x10'``, header 48112 bytes.
  Pixel sizes are stored *largest first*.  Tier LUT slots are 4000 bytes each
  (2000 uint16 entries, max glyph ID 1999), with 4 allocated slots.
* **Version 2** (iOS 9.x) — magic ``b'fcca'``, header 105332 bytes.
  Pixel sizes are stored *smallest first*.  Tier LUT slots are 5000 bytes each
  (2500 uint16 entries, max glyph ID 2499), with 7 allocated slots.

The :attr:`table__a_c_c_f.version` attribute is set to ``1`` or ``2`` on
decompile and used to select the correct wire format on compile.

Version 1 header layout
------------------------
::

    [0x0000] magic          : 4 bytes  = b'\\x40\\x30\\x20\\x10'
    [0x0004] reserved0      : uint32le = 0
    [0x0008] reserved1      : uint32le = 0
    [0x000C] numTiers       : uint32le (e.g. 3 for [96, 64, 40] px)
    [0x0010] storedPixelSizes: uint32le[numTiers]  (largest first)
    [0x0024] numStoredGlyphs: uint32le
    [0x0028] tierGlyphLUTs  : 4 × 4000 bytes
                For tier k: uint16le[2000] at file offset 4000*k + 40
                Entry for glyph_id: global image index, or 0xFFFF if absent.
                Entry at glyph-id 460 (byte offset 920) = notdef fallback.
    [0x3EA8] tierRangeMeta  : 64 bytes (tier start/end/count data)
    [0x3EE8] glyphOffsetTable: uint32le[numStoredGlyphs]
                offset of image record i relative to base 0xBBF0
    [0xBBF0] image records  (variable length, one per stored glyph image)

Version 2 header layout
------------------------
::

    [0x0000] magic          : 4 bytes  = b'fcca'  (LE uint32 0x61636366)
    [0x0004] version        : uint32le = 2
    [0x0008] field3         : uint32le = 1
    [0x000C] numTiers       : uint32le (e.g. 3 for [40, 64, 96] px)
    [0x0010] storedPixelSizes: uint32le[numTiers]  (smallest first)
    [0x002F] resSizeMap     : uint8[161]
                resSizeMap[pxSize] = tier index for the requested pixel size
                (covers sizes 0..160; accessed as data[pxSize + 47])
    [0x00D0] numStoredGlyphs: uint32le
    [0x00D4] tierGlyphLUTs  : 7 × 5000 bytes
                For tier k: uint16le[2500] at file offset 5000*k + 212
                Entry for glyph_id: global image index, or 0xFFFF if absent.
                Entry at glyph-id 460 (byte offset 920) = notdef fallback.
    [0x89AC] tierRangeMeta  : 112 bytes (preserved verbatim)
    [0x89FC] glyphOffsetTable: uint32le[numStoredGlyphs]
                offset of image record i relative to base 0x19B74
    [0x19B74] image records (variable length, one per stored glyph image)

Image record format (identical in both versions)
-------------------------------------------------
::

    [+00] width            : uint32le  (storedPixelSize for this tier)
    [+04] height           : uint32le  (storedPixelSize, always == width)
    [+08] paletteOffset    : uint32le  (= 40, relative to record start)
    [+0C] paletteSizeBytes : uint32le
    [+10] bitsPerPaletteIdx: uint32le  (= ceil(log2(numPalEntries)))
    [+14] runsTableOffset  : uint32le  (relative to record start)
    [+18] reserved0        : uint32le
    [+1C] reserved1        : uint32le  (= 0)
    [+20] bitStreamOffset  : uint32le  (relative to record start)
    [+24] bitStreamBytes   : uint32le

Palette encoding
----------------
Each entry is 21 bits: 7-bit R, 7-bit G, 7-bit B (MSB-first within the
big-endian bit-stream).  8 entries are packed into exactly 21 bytes.
Decoded RGBA: R = r7×2, G = g7×2, B = b7×2, A = from runs table.

Runs table
----------
::

    uint16le numRuns
    For each run:
      uint16le pixelIdx   (flat 1-D index into width×height output buffer)
      uint8    control
      if control & 0x80:   # Mode B – per-pixel alpha
        uint8[control & 0x7F]  alphas
      else:                # Mode A – uniform alpha
        uint8  alpha

Bit-stream (LSB-first within each byte)
----------------------------------------
For each pixel in a run, read a 2-bit opcode:

  ``0b11`` → read ``bitsPerPaletteIdx`` bits for absolute palette index
  ``0b01`` → palette_index += 1
  ``0b10`` → palette_index -= 1
  ``0b00`` → keep palette_index unchanged
"""

import io
import math
import struct
from typing import Dict, List, Optional, Tuple

from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables import DefaultTable

# ── constants ──────────────────────────────────────────────────────────────

MAGIC = b"fcca"

# The header before the first image record is exactly this many bytes.
HEADER_SIZE = 0x19B74  # 105332

# Offset of numStoredGlyphs in the CCF binary.
_OFF_NUM_STORED = 208

# Each tier's glyph-LUT block is 5000 bytes and starts at:
#   file_offset = 5000 * tier_index + 212
_TIER_LUT_BYTES = 5000
_TIER_LUT_BASE = 212

# Maximum glyph IDs per tier-LUT (= 5000 / 2).
_TIER_LUT_MAX_GID = 2500

# Glyph-offset table starts here.
_OFF_GLYPH_OFFSET_TABLE = 0x89FC  # 35324

# Image data starts here.
_OFF_IMAGE_DATA = HEADER_SIZE

# How many tier-LUT blocks are allocated (even if fewer tiers are used).
_NUM_TIER_SLOTS = 7

# The preserved-verbatim "tier range metadata" block between the LUT area and
# the glyph-offset table.
_OFF_TIER_RANGE_META = _TIER_LUT_BASE + _NUM_TIER_SLOTS * _TIER_LUT_BYTES  # 35212

# ── v1 constants (iOS 8.x, magic 0x10203040) ────────────────────────────────
# Version 1 uses a different magic, smaller header, and different LUT layout.
# Stored pixel sizes are in *descending* order (largest tier first).

MAGIC_V1 = b"\x40\x30\x20\x10"  # uint32 LE = 0x10203040

# Fixed header size for v1 (= image data base offset).
HEADER_SIZE_V1 = 48112  # 0xBBF0

# numStoredGlyphs field offset differs between v1 and v2.
_V1_OFF_NUM_STORED = 36

# v1 LUT layout: base=40, 4000 bytes (2000 uint16 entries) per slot, 4 slots.
_V1_LUT_BASE = 40
_V1_LUT_BYTES = 4000
_V1_LUT_MAX_GID = 2000
_V1_NUM_TIER_SLOTS = 4

# 64-byte tier-range metadata block immediately after the 4 LUT slots.
_V1_OFF_TIER_RANGE_META = _V1_LUT_BASE + _V1_NUM_TIER_SLOTS * _V1_LUT_BYTES  # 16040

# Glyph-offset table and image data base for v1.
_V1_OFF_GLYPH_OFFSET_TABLE = 16104   # = _V1_OFF_TIER_RANGE_META + 64
_V1_OFF_IMAGE_DATA = HEADER_SIZE_V1  # 48112

# ── palette helpers ─────────────────────────────────────────────────────────


def _decode_palette(palette_bytes: bytes) -> List[Tuple[int, int, int]]:
    """Decode packed 21-bit-per-entry BGR palette to a list of (R,G,B) tuples.

    Each 21-bit entry stores 7-bit B, 7-bit G, 7-bit R in MSB-first order
    within the big-endian bit-stream.  Values are scaled ×2 (i.e. stored as
    ``b7 << 1``) so that they map directly to the 0-254 range of a uint8.
    """
    n = len(palette_bytes) * 8 // 21
    if n == 0:
        return []

    # Treat the entire palette blob as one big-endian integer.
    total_bits = len(palette_bytes) * 8
    bits = int.from_bytes(palette_bytes, "big")

    result: List[Tuple[int, int, int]] = []
    for i in range(n):
        start = i * 21
        shift = total_bits - start - 21
        if shift < 0:
            break
        entry = (bits >> shift) & 0x1FFFFF  # 21-bit value
        b7 = (entry >> 14) & 0x7F  # MSBs = Blue
        g7 = (entry >> 7) & 0x7F
        r7 = entry & 0x7F          # LSBs = Red
        # Scale 7-bit (0-127) → 8-bit (0-254); max maps to 254 (close to 255).
        result.append((r7 << 1, g7 << 1, b7 << 1))
    return result


def _encode_palette(palette: List[Tuple[int, int, int]]) -> bytes:
    """Encode a list of (R,G,B) 8-bit tuples to the packed 21-bit BGR format.

    The inverse of :func:`_decode_palette`.  Values are shifted right by 1
    before packing (recovering the 7-bit representation); B is placed in the
    MSBs and R in the LSBs.
    """
    n = len(palette)
    total_bits = n * 21
    bits = 0
    total_bit_len = (total_bits + 7) & ~7  # round up to byte boundary

    for i, (r, g, b) in enumerate(palette):
        r7 = (r >> 1) & 0x7F
        g7 = (g >> 1) & 0x7F
        b7 = (b >> 1) & 0x7F
        entry = (b7 << 14) | (g7 << 7) | r7  # Apple packs BGR: B in MSBs, R in LSBs
        shift = total_bit_len - (i + 1) * 21
        bits |= entry << shift

    return bits.to_bytes(total_bit_len // 8, "big")


# ── image decode/encode ─────────────────────────────────────────────────────


def _read_bits_lsb(data: bytes, bit_pos: int, n: int) -> Tuple[int, int]:
    """Read ``n`` bits starting at ``bit_pos`` (LSB-first convention).

    Returns ``(value, new_bit_pos)``.
    """
    val = 0
    for i in range(n):
        byte_idx = (bit_pos + i) >> 3
        bit_idx = (bit_pos + i) & 7
        if byte_idx < len(data):
            val |= ((data[byte_idx] >> bit_idx) & 1) << i
    return val, bit_pos + n


def decode_image_record(record: bytes) -> bytes:
    """Decode a single CCF image record to raw RGBA bytes.

    Parameters
    ----------
    record:
        The raw bytes of one image record (starting from the record header).

    Returns
    -------
    bytes
        Raw ``width × height × 4`` RGBA bytes (top-left origin, row-major).
    """
    if len(record) < 40:
        raise ValueError("Image record too short")

    (width, height, palette_off, palette_size_bytes,
     bits_per_idx, runs_off, _reserved0, _reserved1,
     bitstream_off, bitstream_size) = struct.unpack_from("<IIIIIIIIII", record, 0)

    # ── palette ──
    palette_raw = record[palette_off: palette_off + palette_size_bytes]
    palette = _decode_palette(palette_raw)

    # ── bit-stream ──
    bitstream = record[bitstream_off: bitstream_off + bitstream_size]

    # ── output buffer ──
    output = bytearray(4 * width * height)

    # ── runs table ──
    num_runs = struct.unpack_from("<H", record, runs_off)[0]
    run_pos = runs_off + 2
    bit_pos = 0
    palette_idx = 0

    for _ in range(num_runs):
        pixel_idx = struct.unpack_from("<H", record, run_pos)[0]
        control = record[run_pos + 2]

        if control & 0x80:
            # Mode B: per-pixel alpha
            count = control & 0x7F
            alphas = record[run_pos + 3: run_pos + 3 + count]
            run_pos += 3 + count
        else:
            # Mode A: uniform alpha for all pixels in this run
            count = control  # loop runs `control` times
            alpha_byte = record[run_pos + 3]
            alphas = bytes([alpha_byte]) * count
            run_pos += 4

        for k in range(count):
            # 2-bit opcode (LSB-first)
            opcode, bit_pos = _read_bits_lsb(bitstream, bit_pos, 2)
            if opcode == 3:
                # absolute palette index
                palette_idx, bit_pos = _read_bits_lsb(bitstream, bit_pos, bits_per_idx)
            elif opcode == 1:
                palette_idx += 1
            elif opcode == 2:
                palette_idx -= 1
            # opcode 0: keep current palette_idx

            r, g, b = palette[palette_idx]
            a = alphas[k]
            out_off = (pixel_idx + k) * 4
            output[out_off] = r
            output[out_off + 1] = g
            output[out_off + 2] = b
            output[out_off + 3] = a

    return bytes(output)


def encode_image_record(rgba: bytes, width: int, height: int) -> bytes:
    """Encode raw RGBA bytes to a CCF image record.

    The palette is sorted by pixel frequency so that the most common colour
    occupies index 0.  The bit-stream uses delta opcodes:

    * ``0b00`` (keep) when the palette index is unchanged — costs 2 bits.
    * ``0b01`` (+1) / ``0b10`` (−1) for adjacent index steps — 2 bits each.
    * ``0b11`` (absolute) otherwise — 2 + ``bitsPerPaletteIdx`` bits.

    Runs are split at alpha boundaries: consecutive pixels that share the same
    alpha value are encoded as a single **Mode-A** run (compact 4-byte header
    with one shared alpha byte).  Pixels with varying alpha in a contiguous
    span use **Mode-B** (per-pixel alpha bytes), but the span is truncated as
    soon as two consecutive same-alpha pixels are detected so that they can
    start a fresh Mode-A run.

    The resulting records are significantly more compact than the previous
    single-run absolute-index encoder and closely match Apple-produced sizes.
    """
    total = width * height

    # ── palette: build from non-transparent pixels, sort by frequency ──
    freq: Dict[Tuple[int, int, int], int] = {}
    for i in range(total):
        if rgba[i * 4 + 3] == 0:
            continue        # transparent pixels have no colour in the output
        r = rgba[i * 4    ] & 0xFE
        g = rgba[i * 4 + 1] & 0xFE
        b = rgba[i * 4 + 2] & 0xFE
        c = (r, g, b)
        freq[c] = freq.get(c, 0) + 1
    palette = sorted(freq.keys(), key=lambda c: -freq[c])
    color_to_idx = {c: i for i, c in enumerate(palette)}
    n_colors = len(palette)
    # Minimum bits to address any palette index (corrected from the naive +1 form).
    bits_per_idx = max(1, math.ceil(math.log2(max(n_colors, 1))))
    palette_bytes = _encode_palette(palette)

    # ── collect non-transparent pixels in scan order ──
    # (alpha == 0 pixels are omitted; they default to transparent black in the
    #  output buffer initialised by the decoder)
    pixels: List[Tuple[int, Tuple[int, int, int], int]] = []
    for i in range(total):
        a = rgba[i * 4 + 3]
        if a == 0:
            continue        # skip fully transparent pixels
        r = rgba[i * 4    ] & 0xFE
        g = rgba[i * 4 + 1] & 0xFE
        b = rgba[i * 4 + 2] & 0xFE
        pixels.append((i, (r, g, b), a))

    # ── build runs and bitstream ──
    runs_parts: List[bytes] = []
    bitstream_bits: List[int] = []
    cur_pal_idx = 0

    def append_bits(v: int, n: int) -> None:
        for i in range(n):
            bitstream_bits.append((v >> i) & 1)

    def emit_color(color: Tuple[int, int, int]) -> None:
        nonlocal cur_pal_idx
        new_idx = color_to_idx[color]
        d = new_idx - cur_pal_idx
        if d == 0:
            append_bits(0, 2)            # keep
        elif d == 1:
            append_bits(1, 2)            # +1
        elif d == -1:
            append_bits(2, 2)            # −1
        else:
            append_bits(3, 2)            # absolute
            append_bits(new_idx, bits_per_idx)
        cur_pal_idx = new_idx

    # Walk through pixels grouped into contiguous flat-index segments.
    # Transparent pixels (absent from the list) create segment breaks.
    k = 0
    while k < len(pixels):
        # --- find end of contiguous segment ---
        seg_start = k
        while k + 1 < len(pixels) and pixels[k + 1][0] == pixels[k][0] + 1:
            k += 1
        k += 1
        seg = pixels[seg_start:k]

        # --- emit Mode-A / Mode-B runs within the segment ---
        j = 0
        while j < len(seg):
            alpha = seg[j][2]
            # Find maximal same-alpha run (Mode-A candidate, max 127 pixels).
            m = j + 1
            while m < len(seg) and seg[m][2] == alpha and (m - j) < 127:
                m += 1

            if m - j >= 2:
                # Mode-A: uniform alpha — compact 4-byte run header.
                count = m - j
                runs_parts.append(struct.pack("<HBB", seg[j][0], count, alpha))
                for p in seg[j:m]:
                    emit_color(p[1])
                j = m
            else:
                # Mode-B: collect varying-alpha pixels.  Stop as soon as two
                # consecutive pixels share the same alpha (better as Mode-A).
                mb: List[Tuple[int, Tuple[int, int, int], int]] = [seg[j]]
                j += 1
                while j < len(seg) and len(mb) < 127:
                    if j + 1 < len(seg) and seg[j][2] == seg[j + 1][2]:
                        break
                    mb.append(seg[j])
                    j += 1
                count = len(mb)
                alphas_b = bytes(p[2] for p in mb)
                runs_parts.append(
                    struct.pack("<HB", mb[0][0], 0x80 | count) + alphas_b
                )
                for p in mb:
                    emit_color(p[1])

    # ── pack bitstream (LSB-first bits → bytes) ──
    nbytes = (len(bitstream_bits) + 7) // 8
    bitstream_buf = bytearray(nbytes)
    for b_i, bit in enumerate(bitstream_bits):
        bitstream_buf[b_i >> 3] |= bit << (b_i & 7)
    bitstream_bytes = bytes(bitstream_buf)

    # ── assemble record ──
    HEADER_LEN = 40
    runs_table = struct.pack("<H", len(runs_parts)) + b"".join(runs_parts)
    palette_off = HEADER_LEN
    runs_off = palette_off + len(palette_bytes)
    bitstream_off = runs_off + len(runs_table)
    header = struct.pack(
        "<IIIIIIIIII",
        width,
        height,
        palette_off,
        len(palette_bytes),
        bits_per_idx,
        runs_off,
        0,   # reserved0
        0,   # reserved1
        bitstream_off,
        len(bitstream_bytes),
    )
    assert len(header) == HEADER_LEN
    return header + palette_bytes + runs_table + bitstream_bytes


# ── RGBA ↔ PNG helpers ──────────────────────────────────────────────────────


def _rgba_to_png(rgba: bytes, width: int, height: int) -> bytes:
    """Convert raw RGBA bytes to a PNG byte-string."""
    try:
        from PIL import Image  # type: ignore

        img = Image.frombytes("RGBA", (width, height), rgba)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()
    except ImportError:
        pass

    # Fallback: pure-Python minimal PNG writer.
    return _write_png(rgba, width, height)


def _png_to_rgba(png_data: bytes) -> Tuple[bytes, int, int]:
    """Convert PNG bytes to ``(rgba_bytes, width, height)``."""
    try:
        from PIL import Image  # type: ignore

        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        w, h = img.size
        return img.tobytes(), w, h
    except ImportError:
        pass

    return _read_png(png_data)


def _write_png(rgba: bytes, width: int, height: int) -> bytes:
    """Minimal pure-Python PNG encoder (no external deps)."""
    import zlib

    def make_chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    # IHDR: colour_type=6 (RGBA)
    ihdr = struct.pack(">II", width, height) + bytes([8, 6, 0, 0, 0])

    # IDAT – raw image data with filter type 0 (None) per row
    raw_rows = bytearray()
    row_bytes = width * 4
    for y in range(height):
        raw_rows.append(0)  # filter type = None
        raw_rows += rgba[y * row_bytes: (y + 1) * row_bytes]
    idat_data = zlib.compress(bytes(raw_rows), 9)

    sig = b"\x89PNG\r\n\x1a\n"
    return (sig
            + make_chunk(b"IHDR", ihdr)
            + make_chunk(b"IDAT", idat_data)
            + make_chunk(b"IEND", b""))


def _read_png(png_data: bytes) -> Tuple[bytes, int, int]:
    """Minimal pure-Python PNG reader (RGBA, no filtering/interlacing)."""
    import zlib

    # Parse PNG signature + chunks
    if png_data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG")
    pos = 8
    chunks: Dict[bytes, bytes] = {}
    idat_parts: List[bytes] = []
    while pos < len(png_data):
        length = struct.unpack_from(">I", png_data, pos)[0]
        tag = png_data[pos + 4: pos + 8]
        data = png_data[pos + 8: pos + 8 + length]
        if tag == b"IHDR":
            chunks[tag] = data
        elif tag == b"IDAT":
            idat_parts.append(data)
        elif tag == b"IEND":
            break
        pos += 12 + length

    ihdr = chunks[b"IHDR"]
    width = struct.unpack_from(">I", ihdr, 0)[0]
    height = struct.unpack_from(">I", ihdr, 4)[0]
    bit_depth = ihdr[8]
    colour_type = ihdr[9]

    if bit_depth != 8 or colour_type != 6:
        raise ValueError("Only 8-bit RGBA PNG supported in fallback reader")

    raw = zlib.decompress(b"".join(idat_parts))
    row_bytes = width * 4
    rgba = bytearray(width * height * 4)
    for y in range(height):
        filter_type = raw[y * (row_bytes + 1)]
        if filter_type != 0:
            raise ValueError("PNG filter types other than None (0) not supported")
        row = raw[y * (row_bytes + 1) + 1: y * (row_bytes + 1) + 1 + row_bytes]
        rgba[y * row_bytes: (y + 1) * row_bytes] = row
    return bytes(rgba), width, height


# ── CcfGlyph ────────────────────────────────────────────────────────────────


class CcfGlyph:
    """A single glyph image within a :class:`CcfStrike`.

    Attributes
    ----------
    glyphName : str
    imageData : bytes
        PNG-encoded image data.
    """

    def __init__(
        self,
        glyphName: str = "",
        imageData: Optional[bytes] = None,
        rawRecordData: Optional[bytes] = None,
    ):
        self.glyphName = glyphName
        self._imageData = imageData
        self._rawRecordData = rawRecordData

    @property
    def rawRecordData(self) -> Optional[bytes]:
        """Raw CCF image-record bytes, available only while the glyph has not
        been decoded or externally modified.  Returns ``None`` once
        :attr:`imageData` has been accessed or assigned."""
        return self._rawRecordData

    @property
    def imageData(self) -> Optional[bytes]:
        """PNG image bytes, decoded from the raw CCF record on first access."""
        if self._imageData is None and self._rawRecordData is not None:
            rgba = decode_image_record(self._rawRecordData)
            w = struct.unpack_from("<I", self._rawRecordData, 0)[0]
            h = struct.unpack_from("<I", self._rawRecordData, 4)[0]
            self._imageData = _rgba_to_png(rgba, w, h)
            self._rawRecordData = None  # free raw bytes
        return self._imageData

    @imageData.setter
    def imageData(self, value: bytes):
        self._imageData = value
        self._rawRecordData = None

    def toXML(self, writer, ttFont, **kwargs):
        import base64

        attrs = [("name", self.glyphName)]
        data = self.imageData
        if data:
            writer.begintag("glyph", attrs)
            writer.newline()
            encoded = base64.b64encode(data).decode("ascii")
            # Write in 76-char lines
            for i in range(0, len(encoded), 76):
                writer.write(encoded[i: i + 76])
                writer.newline()
            writer.endtag("glyph")
        else:
            writer.simpletag("glyph", attrs)
        writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        import base64

        if name == "glyph":
            self.glyphName = attrs.get("name", self.glyphName)
            raw_b64 = "".join(
                item for item in content if isinstance(item, str)
            ).strip()
            if raw_b64:
                self._imageData = base64.b64decode(raw_b64)
                self._rawRecordData = None


# ── CcfStrike ───────────────────────────────────────────────────────────────


class CcfStrike:
    """One resolution tier (stored pixel size) within an ``accf`` table.

    Attributes
    ----------
    pixelSize : int
        The stored pixel size (width = height) for all images in this strike.
    glyphs : dict[str, CcfGlyph]
        Maps glyph name → :class:`CcfGlyph`.
    """

    def __init__(self, pixelSize: int = 0):
        self.pixelSize = pixelSize
        self.glyphs: Dict[str, CcfGlyph] = {}

    def toXML(self, writer, ttFont, **kwargs):
        writer.begintag("strike", [("pixelSize", self.pixelSize)])
        writer.newline()
        glyphOrder = ttFont.getGlyphOrder()
        for glyphName in glyphOrder:
            if glyphName in self.glyphs:
                self.glyphs[glyphName].toXML(writer, ttFont)
        writer.endtag("strike")
        writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == "pixelSize":
            self.pixelSize = safeEval(attrs["value"])
        elif name == "glyph":
            glyph = CcfGlyph()
            glyph.fromXML(name, attrs, content, ttFont)
            self.glyphs[glyph.glyphName] = glyph


# ── main table class ─────────────────────────────────────────────────────────


class table__a_c_c_f(DefaultTable.DefaultTable):
    """Apple Color Compressed Font (``accf``) table.

    This table stores compressed colour bitmap images for emoji (or other
    colour glyphs) using a proprietary palette + run-length encoding.

    The table is represented as a collection of :class:`CcfStrike` objects
    (one per stored pixel size / resolution tier).

    See the module docstring for a detailed format description.
    """

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.version = 2
        self.field3 = 1
        self.strikes: Dict[int, CcfStrike] = {}  # pixelSize → CcfStrike
        # Verbatim copy of the CCF header blob (bytes 0-105331).  Preserved
        # so that compile() can reproduce an identical binary when no edits
        # have been made.
        self._rawHeader: Optional[bytes] = None

    # ── decompile ────────────────────────────────────────────────────────────

    def decompile(self, data: bytes, ttFont):
        magic = data[0:4]
        if magic == MAGIC:
            # ── v2 ──────────────────────────────────────────────────────────
            if len(data) < HEADER_SIZE + 1:
                raise ValueError(
                    f"accf data too short: expected ≥ {HEADER_SIZE + 1}, got {len(data)}"
                )
            self.version = struct.unpack_from("<I", data, 4)[0]
            self.field3 = struct.unpack_from("<I", data, 8)[0]
            hdr_size = HEADER_SIZE
            lut_base = _TIER_LUT_BASE
            lut_bytes = _TIER_LUT_BYTES
            lut_max_gid = _TIER_LUT_MAX_GID
            off_gt = _OFF_GLYPH_OFFSET_TABLE
            off_img = _OFF_IMAGE_DATA
        elif magic == MAGIC_V1:
            # ── v1 ──────────────────────────────────────────────────────────
            if len(data) < HEADER_SIZE_V1 + 1:
                raise ValueError(
                    f"accf data too short: expected ≥ {HEADER_SIZE_V1 + 1}, got {len(data)}"
                )
            self.version = 1
            self.field3 = 0
            hdr_size = HEADER_SIZE_V1
            lut_base = _V1_LUT_BASE
            lut_bytes = _V1_LUT_BYTES
            lut_max_gid = _V1_LUT_MAX_GID
            off_gt = _V1_OFF_GLYPH_OFFSET_TABLE
            off_img = _V1_OFF_IMAGE_DATA
        else:
            raise ValueError(
                f"accf: bad magic {magic!r}, expected {MAGIC!r} (v2) or {MAGIC_V1!r} (v1)"
            )

        num_tiers = struct.unpack_from("<I", data, 12)[0]
        stored_sizes = [
            struct.unpack_from("<I", data, 16 + 4 * i)[0] for i in range(num_tiers)
        ]

        # Stash the header for compile() round-trips.
        self._rawHeader = data[:hdr_size]

        # Build glyph-order map: glyph_name → glyph_id
        glyph_order = ttFont.getGlyphOrder()
        gid_to_name = {gid: name for gid, name in enumerate(glyph_order)}

        # For each tier, build a mapping: glyph_name → raw image record bytes
        for tier_idx, pixel_size in enumerate(stored_sizes):
            strike = CcfStrike(pixelSize=pixel_size)

            max_gid = min(len(glyph_order), lut_max_gid)
            for gid in range(max_gid):
                lut_off = lut_base + lut_bytes * tier_idx + 2 * gid
                if lut_off + 2 > len(data):
                    break
                global_img_idx = struct.unpack_from("<H", data, lut_off)[0]
                if global_img_idx == 0xFFFF:
                    continue  # no image for this glyph in this tier

                record = _get_image_record(data, global_img_idx, off_gt, off_img)
                if record is None:
                    continue

                glyph_name = gid_to_name.get(gid)
                if glyph_name is None:
                    continue

                strike.glyphs[glyph_name] = CcfGlyph(
                    glyphName=glyph_name,
                    rawRecordData=record,
                )

            self.strikes[pixel_size] = strike


    # ── compile ──────────────────────────────────────────────────────────────

    def compile(self, ttFont) -> bytes:
        """Serialise the table back to the CCF binary format."""
        glyph_order = ttFont.getGlyphOrder()
        name_to_gid = {name: gid for gid, name in enumerate(glyph_order)}

        if self.version == 1:
            # v1: sizes stored largest-first; different structural constants
            sorted_sizes = sorted(self.strikes.keys(), reverse=True)
            hdr_size = HEADER_SIZE_V1
            lut_base = _V1_LUT_BASE
            lut_bytes = _V1_LUT_BYTES
            lut_max_gid = _V1_LUT_MAX_GID
            num_tier_slots = _V1_NUM_TIER_SLOTS
            off_gt = _V1_OFF_GLYPH_OFFSET_TABLE
            off_num_stored = _V1_OFF_NUM_STORED
        else:
            # v2: sizes stored smallest-first
            sorted_sizes = sorted(self.strikes.keys())
            hdr_size = HEADER_SIZE
            lut_base = _TIER_LUT_BASE
            lut_bytes = _TIER_LUT_BYTES
            lut_max_gid = _TIER_LUT_MAX_GID
            num_tier_slots = _NUM_TIER_SLOTS
            off_gt = _OFF_GLYPH_OFFSET_TABLE
            off_num_stored = _OFF_NUM_STORED

        num_tiers = len(sorted_sizes)

        # Build global image list and per-tier LUTs.
        # Images are laid out as: all tier-0 images, then tier-1, then tier-2, …
        all_records: List[bytes] = []  # indexed by global_image_index
        tier_luts: List[Dict[int, int]] = [{} for _ in range(num_tiers)]

        for tier_idx, pixel_size in enumerate(sorted_sizes):
            strike = self.strikes[pixel_size]
            tier_luts[tier_idx] = {}

            for glyph_name, glyph in strike.glyphs.items():
                gid = name_to_gid.get(glyph_name)
                if gid is None or gid >= lut_max_gid:
                    continue
                # Use the original record bytes if the glyph was never edited
                # (avoids lossy re-encoding and gives exact binary reproduction).
                raw = glyph.rawRecordData
                if raw is not None:
                    record = raw
                else:
                    image_data = glyph.imageData
                    if image_data is None:
                        continue
                    rgba, w, h = _png_to_rgba(image_data)
                    record = encode_image_record(rgba, w, h)
                global_idx = len(all_records)
                all_records.append(record)
                tier_luts[tier_idx][gid] = global_idx

        num_stored = len(all_records)

        # ── Build the fixed-size header ──────────────────────────────────────
        header = bytearray(hdr_size)

        # Seed from cached original header to preserve verbatim metadata.
        if self._rawHeader is not None and len(self._rawHeader) == hdr_size:
            header[:] = self._rawHeader

        if self.version == 1:
            header[0:4] = MAGIC_V1
            header[4:12] = b"\x00" * 8
            struct.pack_into("<I", header, 12, num_tiers)
            for i, sz in enumerate(sorted_sizes):
                struct.pack_into("<I", header, 16 + 4 * i, sz)
            struct.pack_into("<I", header, off_num_stored, num_stored)
            if self._rawHeader is None:
                _build_v1_tier_range_meta(header, tier_luts)
        else:
            struct.pack_into("<4sIII", header, 0, MAGIC, self.version, self.field3, num_tiers)
            for i, sz in enumerate(sorted_sizes):
                struct.pack_into("<I", header, 16 + 4 * i, sz)
            struct.pack_into("<I", header, off_num_stored, num_stored)
            if self._rawHeader is None:
                _build_resolution_map(header, sorted_sizes)

        # Clear and rebuild all tier LUTs.
        # Active tiers: sentinel 0xFFFF then patch in known indices.
        # Unused tier slots: zero-fill (Apple's convention for unallocated slots).
        for tier_idx in range(num_tier_slots):
            slot_base = lut_base + lut_bytes * tier_idx
            if tier_idx < num_tiers:
                # Active tier — fill with no-image sentinel, then write real indices.
                header[slot_base: slot_base + lut_bytes] = b"\xff" * lut_bytes
                for gid, global_idx in tier_luts[tier_idx].items():
                    struct.pack_into("<H", header, slot_base + 2 * gid, global_idx)
            else:
                # Unused tier — zeros (matches Apple-produced files).
                header[slot_base: slot_base + lut_bytes] = b"\x00" * lut_bytes

        # Glyph offset table + image data section.
        # Identical records (same bytes) share one physical copy — this
        # reproduces Apple's image deduplication and keeps file sizes compact.
        record_to_phys: Dict[bytes, int] = {}  # content → byte offset from IMG_BASE
        unique_buf: List[bytes] = []
        phys_cumulative = 0
        global_phys_offsets: List[int] = []    # global_idx → physical offset

        for record in all_records:
            if record in record_to_phys:
                global_phys_offsets.append(record_to_phys[record])
            else:
                record_to_phys[record] = phys_cumulative
                unique_buf.append(record)
                global_phys_offsets.append(phys_cumulative)
                phys_cumulative += len(record)

        for i, phys_off in enumerate(global_phys_offsets):
            off_in_table = off_gt + 4 * i
            if off_in_table + 4 <= hdr_size:
                struct.pack_into("<I", header, off_in_table, phys_off)

        return bytes(header) + b"".join(unique_buf)

    # ── XML ──────────────────────────────────────────────────────────────────

    def toXML(self, writer, ttFont, **kwargs):
        writer.simpletag("version", value=self.version)
        writer.newline()
        for ps in sorted(self.strikes.keys()):
            self.strikes[ps].toXML(writer, ttFont)

    def fromXML(self, name, attrs, content, ttFont):
        if name == "version":
            self.version = safeEval(attrs["value"])
        elif name == "strike":
            strike = CcfStrike()
            # pixelSize is an attribute of the <strike> element
            if "pixelSize" in attrs:
                strike.pixelSize = safeEval(str(attrs["pixelSize"]))
            for element in content:
                if isinstance(element, tuple):
                    ename, eattrs, econtent = element
                    strike.fromXML(ename, eattrs, econtent, ttFont)
            self.strikes[strike.pixelSize] = strike
        else:
            from fontTools import ttLib

            raise ttLib.TTLibError(f"Unknown accf XML element: {name!r}")


# ── private helpers ─────────────────────────────────────────────────────────


def _get_image_record(
    data: bytes,
    global_img_idx: int,
    off_table: int = _OFF_GLYPH_OFFSET_TABLE,
    img_base: int = _OFF_IMAGE_DATA,
) -> Optional[bytes]:
    """Return the raw bytes of image record ``global_img_idx``, or ``None``."""
    offset_table_entry = off_table + 4 * global_img_idx
    if offset_table_entry + 4 > len(data):
        return None
    rel_offset = struct.unpack_from("<I", data, offset_table_entry)[0]
    abs_start = img_base + rel_offset

    if abs_start + 40 > len(data):
        return None

    # Determine record length from fields in its header
    bitstream_off = struct.unpack_from("<I", data, abs_start + 32)[0]
    bitstream_size = struct.unpack_from("<I", data, abs_start + 36)[0]
    record_size = bitstream_off + bitstream_size
    if abs_start + record_size > len(data):
        record_size = len(data) - abs_start

    return data[abs_start: abs_start + record_size]


def _build_v1_tier_range_meta(
    header: bytearray,
    tier_luts: List[Dict[int, int]],
) -> None:
    """Populate the 64-byte tier-range metadata block for v1 format.

    The block consists of 16 uint32LE values in four groups of 4 (one per slot):
      - tier_start[0..3]:  global image index of first image in each tier
      - tier_last[0..3]:   global image index of last image in each tier
      - tier_cap[0..3]:    capacity (set equal to count for new tables)
      - tier_count[0..3]:  actual image count in each tier
    """
    counts = [len(lut) for lut in tier_luts]
    # Pad to _V1_NUM_TIER_SLOTS slots
    while len(counts) < _V1_NUM_TIER_SLOTS:
        counts.append(0)

    starts = []
    ends = []
    cumulative = 0
    for c in counts:
        starts.append(cumulative)
        ends.append(cumulative + c - 1 if c > 0 else 0)
        cumulative += c

    off = _V1_OFF_TIER_RANGE_META
    for i, v in enumerate(starts):
        struct.pack_into("<I", header, off + 4 * i, v)
    for i, v in enumerate(ends):
        struct.pack_into("<I", header, off + 4 * (_V1_NUM_TIER_SLOTS + i), v)
    for i, v in enumerate(counts):
        struct.pack_into("<I", header, off + 4 * (2 * _V1_NUM_TIER_SLOTS + i), v)
    for i, v in enumerate(counts):
        struct.pack_into("<I", header, off + 4 * (3 * _V1_NUM_TIER_SLOTS + i), v)


def _build_resolution_map(header: bytearray, sorted_sizes: List[int]):
    """Populate the 161-byte resolution-class lookup table at bytes 47..207.

    ``header[pxSize + 47] = tier_index`` for all pxSize in 0..160.
    The thresholds are computed as the midpoint between adjacent tier sizes.
    """
    num_tiers = len(sorted_sizes)
    # Assign each pixel size 0..160 to the nearest tier (round up to next tier)
    for px in range(161):
        best = 0
        for ti, sz in enumerate(sorted_sizes):
            if px <= sz:
                best = ti
                break
        else:
            best = num_tiers - 1
        off = px + 47
        if off < HEADER_SIZE:
            header[off] = best
