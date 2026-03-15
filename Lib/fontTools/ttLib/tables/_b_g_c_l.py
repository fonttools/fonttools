"""Support for the `bgcl` (Apple Color Emoji background) table.

This table stores a JSON blob. We decode it to a Python object on
decompile and emit human readable JSON in the TTX via a <json> element.
On compile we re-encode the JSON to UTF-8 bytes which is what Apple code
reads via CTFontCopyTable then JSONDecoder.

On iOS 16 and later the `bgcl` payload is used as the wallpaper
background color when the user selects an emoji wallpaper.

This implementation is intentionally lightweight: it preserves the JSON
structure and exposes convenience attributes `colors`, `emojicolors`,
`indexmap` and `version` when available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fontTools.misc.textTools import tostr, strjoin
from . import DefaultTable
import json

if TYPE_CHECKING:
    from fontTools.misc.xmlWriter import XMLWriter
    from fontTools.ttLib import TTFont


class table__b_g_c_l(DefaultTable.DefaultTable):
    """bgcl table: stores a JSON blob describing background palettes.

    The JSON structure typically contains the top-level keys:
      - colors: [[R,G,B,A], ...]
      - emojicolors: [[[dominant...],[accent...],[contextual...]], ...]
      - indexmap: {"glyphIndex": emojicolors_index, ...}
      - version: int
    """

    def decompile(self, data: bytes, ttFont: TTFont) -> None:
        """Store raw bytes and attempt to parse JSON.

        The JSON commonly includes palette/lookup data used at runtime to
        construct wallpaper/background colors for emoji wallpapers on
        recent iOS releases.
        """
        self.data = data
        try:
            text = tostr(data, "utf_8")
            self.json = json.loads(text)
        except Exception as e:  # keep table decompilation robust
            self.json = None
            self.ERROR = f"bgcl JSON parse error: {e!r}"
            return
        # convenient attributes
        self.colors = self.json.get("colors")
        self.emojicolors = self.json.get("emojicolors")
        self.indexmap = self.json.get("indexmap")
        self.version = self.json.get("version")

    def compile(self, ttFont: TTFont) -> bytes:
        """Encode the JSON object to UTF-8 bytes for font binary storage."""
        if getattr(self, "json", None) is None:
            # fallback to raw bytes if parsing failed earlier
            return getattr(self, "data", b"")
        # use compact representation for binary table
        return json.dumps(self.json, separators=(",", ":"), ensure_ascii=False).encode(
            "utf_8"
        )

    def toXML(self, writer: XMLWriter, ttFont: TTFont) -> None:
        """Emit pretty-printed JSON inside a <json> element for human inspection."""
        if getattr(self, "json", None) is None:
            # fallback to default hex output
            DefaultTable.DefaultTable.toXML(self, writer, ttFont)
            return
        writer.begintag("json")
        writer.newline()
        pretty = json.dumps(self.json, indent=2, ensure_ascii=False)
        writer.writecdata(pretty)
        writer.newline()
        writer.endtag("json")
        writer.newline()

    def fromXML(
        self, name: str, attrs: dict[str, str], content, ttFont: TTFont
    ) -> None:
        """Read JSON from the <json> element. `content` may be a list.

        This mirrors SVG/other table `fromXML` handlers which accept a
        list of content chunks.
        """
        if name != "json":
            # fall back to DefaultTable behavior for unknown elements
            return DefaultTable.DefaultTable.fromXML(self, name, attrs, content, ttFont)
        text = strjoin(content).strip()
        try:
            self.json = json.loads(text)
            # keep raw bytes in sync
            self.data = text.encode("utf_8")
            self.colors = self.json.get("colors")
            self.emojicolors = self.json.get("emojicolors")
            self.indexmap = self.json.get("indexmap")
            self.version = self.json.get("version")
        except Exception as e:
            # store error and fall back to raw
            self.json = None
            self.ERROR = f"bgcl JSON parse error in fromXML: {e!r}"
