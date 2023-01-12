# Modified from https://github.com/adobe-type-tools/psautohint/blob/08b346865710ed3c172f1eb581d6ef243b203f99/python/psautohint/ufoFont.py#L800-L838
from __future__ import annotations
import hashlib
from typing import Any

from fontTools.pens.basePen import MissingComponentError
from fontTools.pens.pointPen import AbstractPointPen
from fontTools.pens.typings import GlyphSet, Point, PointType, Transformation


class HashPointPen(AbstractPointPen):
    """
    This pen can be used to check if a glyph's contents (outlines plus
    components) have changed.

    Components are added as the original outline plus each composite's
    transformation.

    Example: You have some TrueType hinting code for a glyph which you want to
    compile. The hinting code specifies a hash value computed with HashPointPen
    that was valid for the glyph's outlines at the time the hinting code was
    written. Now you can calculate the hash for the glyph's current outlines to
    check if the outlines have changed, which would probably make the hinting
    code invalid.

    > glyph = ufo[name]
    > hash_pen = HashPointPen(glyph.width, ufo)
    > glyph.drawPoints(hash_pen)
    > ttdata = glyph.lib.get("public.truetype.instructions", None)
    > stored_hash = ttdata.get("id", None)  # The hash is stored in the "id" key
    > if stored_hash is None or stored_hash != hash_pen.hash:
    >    logger.error(f"Glyph hash mismatch, glyph '{name}' will have no instructions in font.")
    > else:
    >    # The hash values are identical, the outline has not changed.
    >    # Compile the hinting code ...
    >    pass
    """

    def __init__(self, glyphWidth: int = 0, glyphSet: GlyphSet | None = None) -> None:
        self.glyphset = glyphSet
        self.data = ["w%s" % round(glyphWidth, 9)]

    @property
    def hash(self) -> str:
        data = "".join(self.data)
        if len(data) >= 128:
            data = hashlib.sha512(data.encode("ascii")).hexdigest()
        return data

    def beginPath(self, identifier: str | None = None, **kwargs: Any) -> None:
        pass

    def endPath(self) -> None:
        self.data.append("|")

    def addPoint(
        self,
        pt: Point,
        segmentType: PointType = None,
        smooth: bool = False,
        name: str | None = None,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        if segmentType is None:
            pt_type = "o"  # offcurve
        else:
            pt_type = segmentType[0]
        self.data.append(f"{pt_type}{pt[0]:g}{pt[1]:+g}")

    def addComponent(
        self,
        baseGlyphName: str,
        transformation: Transformation,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        tr = "".join([f"{t:+}" for t in transformation])
        self.data.append("[")
        try:
            assert self.glyphset is not None
            self.glyphset[baseGlyphName].drawPoints(self)
        except KeyError:
            raise MissingComponentError(baseGlyphName)
        self.data.append(f"({tr})]")
