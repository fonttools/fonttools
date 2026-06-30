"""Apple 'cntr' (Emoji Centering Data) table support.

The ``cntr`` table is an Apple proprietary table used in color emoji fonts
(e.g., AppleColorEmoji). Its payload is a UTF-8 encoded JSON object with the
following top-level structure::

    {
        "version": 1,
        "size":    [<width>, <height>],
        "profiles": {
            "<glyphID>": [
                [<left>, <bottom>, <right>, <top>],   // pixel bounding-box (ints)
                [<dx>, <dy>]                          // centering offsets (floats)
            ],
            ...
        }
    }

``version`` is always 1 in observed fonts.  ``size`` is the square canvas size
of the emoji bitmap (typically ``[160, 160]``).  Each ``profiles`` entry maps a
glyph ID (as a decimal string) to a two-element array: the tight pixel
bounding-box of the rendered emoji on that canvas, and the horizontal/vertical
centering adjustment.

This is decoded on-device by the iOS/macOS *EmojiFoundation* framework using
``CTFontCopyTable`` with the ``'cntr'`` tag and then ``JSONDecoder`` into the
``EmojiCenteringData`` Swift type.

TTX XML structure
-----------------

.. code-block:: xml

    <cntr>
      <version value="1"/>
      <size width="160" height="160"/>
      <profiles>
        <profile name="uni1F600" left="12" bottom="1" right="148" top="158"
                 dx="0.07873167406656933" dy="-0.013258938485454144"/>
        ...
      </profiles>
    </cntr>

Each ``<profile>`` element uses the glyph *name* (from the font's glyph order)
rather than the raw integer glyph ID, consistent with the fontTools TTX
convention.  When the glyph name is unavailable (e.g. the glyph order is not
loaded), the attribute ``glyphID`` is used as a fallback on both read and
write.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from . import DefaultTable

if TYPE_CHECKING:
    from typing import Any

    from fontTools.misc.xmlWriter import XMLWriter
    from fontTools.ttLib import TTFont


class table__c_n_t_r(DefaultTable.DefaultTable):
    """Apple Emoji Centering Data table.

    Stores per-glyph pixel bounding boxes and centering offsets for
    Apple's color emoji fonts.  The on-disk payload is a UTF-8 JSON blob.
    """

    def __init__(self, tag: str | bytes | None = None) -> None:
        DefaultTable.DefaultTable.__init__(self, tag)
        self.version: int = 1
        self.size: list[int] = [160, 160]
        # profiles: {glyphName: {"bbox": [l, b, r, t], "offset": [dx, dy]}}
        self.profiles: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Compile / decompile
    # ------------------------------------------------------------------

    def decompile(self, data: bytes, ttFont: TTFont) -> None:
        payload = json.loads(data.decode("utf-8"))
        self.version = int(payload.get("version", 1))
        self.size = list(payload.get("size", [160, 160]))
        self.profiles = {}
        glyphOrder = ttFont.getGlyphOrder() if ttFont is not None else []
        for gid_str, (bbox, offset) in payload.get("profiles", {}).items():
            gid = int(gid_str)
            if gid < len(glyphOrder):
                key = glyphOrder[gid]
            else:
                key = gid_str
            self.profiles[key] = {
                "bbox": [int(v) for v in bbox],
                # Preserve the original int/float distinction so that
                # integer zeros serialise as "0" rather than "0.0".
                "offset": list(offset),
            }

    def compile(self, ttFont: TTFont) -> bytes:
        glyphOrder = ttFont.getGlyphOrder() if ttFont is not None else []
        glyphIndexMap: dict[str, int] = {name: i for i, name in enumerate(glyphOrder)}
        profiles: dict[str, list] = {}
        for key, entry in self.profiles.items():
            if key in glyphIndexMap:
                gid_str = str(glyphIndexMap[key])
            else:
                # key is already a raw glyph-ID string (fallback)
                gid_str = key
            profiles[gid_str] = [entry["bbox"], entry["offset"]]
        payload = {
            "profiles": profiles,
            "size": self.size,
            "version": self.version,
        }
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

    # ------------------------------------------------------------------
    # TTX import / export
    # ------------------------------------------------------------------

    def toXML(self, writer: XMLWriter, ttFont: TTFont, **kwargs) -> None:
        writer.simpletag("version", value=self.version)
        writer.newline()
        writer.simpletag("size", width=self.size[0], height=self.size[1])
        writer.newline()
        writer.begintag("profiles")
        writer.newline()
        glyphOrder = ttFont.getGlyphOrder() if ttFont is not None else []
        glyphIndexMap: dict[str, int] = {name: i for i, name in enumerate(glyphOrder)}
        for name, entry in self.profiles.items():
            bbox = entry["bbox"]
            dx, dy = entry["offset"]
            attrs: dict[str, Any]
            if name in glyphIndexMap:
                attrs = {"name": name}
            else:
                attrs = {"glyphID": name}
            # Use repr() for floats to get round-trip-exact representation;
            # pass integers through as-is so "0" doesn't become "0.0".
            attrs.update(
                {
                    "left": bbox[0],
                    "bottom": bbox[1],
                    "right": bbox[2],
                    "top": bbox[3],
                    "dx": repr(dx) if isinstance(dx, float) else dx,
                    "dy": repr(dy) if isinstance(dy, float) else dy,
                }
            )
            writer.simpletag("profile", **attrs)
            writer.newline()
        writer.endtag("profiles")
        writer.newline()

    def fromXML(
        self, name: str, attrs: dict[str, str], content: str, ttFont: TTFont
    ) -> None:
        if name == "version":
            self.version = int(attrs["value"])
        elif name == "size":
            self.size = [int(attrs["width"]), int(attrs["height"])]
        elif name == "profiles":
            for element in content:
                if not isinstance(element, tuple):
                    continue
                ename, eattrs, econtent = element
                if ename != "profile":
                    continue
                if "name" in eattrs:
                    key = eattrs["name"]
                else:
                    key = eattrs["glyphID"]
                bbox = [
                    int(eattrs["left"]),
                    int(eattrs["bottom"]),
                    int(eattrs["right"]),
                    int(eattrs["top"]),
                ]
                # Use safeEval so that "0" stays as int 0 and "0.5" becomes
                # float 0.5, matching the original JSON serialisation.
                from fontTools.misc.textTools import safeEval

                offset = [safeEval(eattrs["dx"]), safeEval(eattrs["dy"])]
                self.profiles[key] = {"bbox": bbox, "offset": offset}
