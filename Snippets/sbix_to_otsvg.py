#!/usr/bin/env python3

"""Convert one PNG strike from an sbix font to a bitmap-backed SVG table.

The output has one SVG document per glyph. Each document embeds the explicitly
selected strike's PNG as a data URL. OpenType SVG has no strike-selection
mechanism, so exactly one sbix strike is converted.

Requires fonttools and Pillow. WOFF2 output also requires Brotli.
"""

from __future__ import annotations

import argparse
import base64
from io import BytesIO
import logging
from pathlib import Path
import sys
from typing import Any, cast

from fontTools import configLogger
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.S_V_G_ import SVGDocument
from PIL import Image

SBIX_DRAW_OUTLINES = 1 << 1
log = logging.getLogger(__name__)


def _png_dimensions(data: bytes, glyph_name: str) -> tuple[int, int]:
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != "PNG":
                raise ValueError(
                    f"{glyph_name!r} contains {image.format or 'unknown'} data, not PNG"
                )
            width, height = image.size
            image.verify()
    except (OSError, SyntaxError, ValueError) as error:
        raise ValueError(f"{glyph_name!r} contains invalid PNG data") from error
    if width == 0 or height == 0:
        raise ValueError(f"{glyph_name!r} has invalid PNG dimensions {width}x{height}")
    return width, height


def _resolve_png_data(strike, glyph_name: str, chain: tuple[str, ...] = ()):
    glyph = strike.glyphs.get(glyph_name)
    if glyph is None or glyph.graphicType is None:
        if chain:
            path = " -> ".join((*chain, glyph_name))
            raise ValueError(f"broken sbix dupe reference: {path}")
        return None

    graphic_type = glyph.graphicType.rstrip("\0 ")
    if graphic_type == "dupe":
        reference_name = glyph.referenceGlyphName
        if reference_name is None:
            raise ValueError(f"{glyph_name!r} has a dupe record without a reference")
        if reference_name == glyph_name or reference_name in chain:
            path = " -> ".join((*chain, glyph_name, reference_name))
            raise ValueError(f"cyclic sbix dupe reference: {path}")
        return _resolve_png_data(strike, reference_name, (*chain, glyph_name))

    if graphic_type != "png":
        raise ValueError(
            f"{glyph_name!r} uses unsupported sbix graphic type "
            f"{glyph.graphicType!r}; only PNG and dupe records are supported"
        )
    if glyph.imageData is None:
        raise ValueError(f"{glyph_name!r} has a PNG record without image data")
    return glyph.imageData


def _number(value: float) -> str:
    value = round(value, 6)
    if value == 0:
        return "0"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _svg_document(
    glyph_id: int,
    image_data: bytes,
    x: float,
    y: float,
    width: float,
    height: float,
) -> str:
    encoded = base64.b64encode(image_data).decode("ascii")
    return (
        f'<svg id="glyph{glyph_id}" version="1.1" '
        'xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink">'
        f'<image x="{_number(x)}" y="{_number(y)}" '
        f'width="{_number(width)}" height="{_number(height)}" '
        f'xlink:href="data:image/png;base64,{encoded}"/>'
        "</svg>"
    )


def convert_sbix_to_otsvg(
    font: TTFont,
    ppem: int | None = None,
    *,
    compress_documents: bool = False,
    keep_sbix: bool = False,
    replace_svg: bool = False,
) -> tuple[int, int]:
    if "sbix" not in font:
        raise ValueError("input font has no 'sbix' table")
    if "glyf" not in font:
        raise ValueError("only sbix fonts with TrueType 'glyf' outlines are supported")

    sbix = cast(Any, font["sbix"])
    strikes = sbix.strikes
    if not strikes:
        raise ValueError("input font has an empty 'sbix' table")
    if ppem is None:
        available = ", ".join(str(value) for value in sorted(strikes))
        raise ValueError(
            f"--ppem is required; available sbix strike PPEMs: {available}; "
            "rerun with --ppem <value>"
        )
    if "SVG " in font and not replace_svg:
        raise ValueError(
            "input font already has an 'SVG ' table; use --replace-svg to replace it"
        )
    if ppem not in strikes:
        available = ", ".join(str(value) for value in sorted(strikes))
        raise ValueError(f"no sbix strike at ppem {ppem}; available: {available}")
    if sbix.flags & SBIX_DRAW_OUTLINES:
        log.warning(
            "sbix flags bit 1 (draw outlines) is set; the OT-SVG output "
            "preserves the bitmap but not the outline overlay"
        )

    strike = strikes[ppem]
    units_per_pixel = cast(Any, font["head"]).unitsPerEm / ppem
    glyf = font["glyf"]
    documents = []

    for glyph_id, glyph_name in enumerate(font.getGlyphOrder()):
        sbix_glyph = strike.glyphs.get(glyph_name)
        if sbix_glyph is None or sbix_glyph.graphicType is None:
            continue

        image_data = _resolve_png_data(strike, glyph_name)
        if image_data is None:
            continue
        width_px, height_px = _png_dimensions(image_data, glyph_name)

        outline = glyf[glyph_name]
        if getattr(outline, "numberOfContours", 0) != 0:
            if not hasattr(outline, "xMin"):
                outline.recalcBounds(glyf)
            origin_x = outline.xMin
            origin_y = outline.yMin
        else:
            origin_x = 0
            origin_y = 0

        # sbix offsets and dimensions are on the strike's pixel grid. Convert
        # them to font units. sbix positions the bitmap's bottom edge in a y-up
        # coordinate system; SVG positions its top edge in a y-down system.
        x = origin_x + sbix_glyph.originOffsetX * units_per_pixel
        bottom = origin_y + sbix_glyph.originOffsetY * units_per_pixel
        width = width_px * units_per_pixel
        height = height_px * units_per_pixel
        y = -(bottom + height)

        documents.append(
            SVGDocument(
                _svg_document(glyph_id, image_data, x, y, width, height),
                glyph_id,
                glyph_id,
                compress_documents,
            )
        )

    if not documents:
        raise ValueError(f"sbix strike at ppem {ppem} contains no PNG glyphs")

    svg_table = cast(Any, newTable("SVG "))
    svg_table.docList = documents
    font["SVG "] = svg_table
    if not keep_sbix:
        del font["sbix"]
    return ppem, len(documents)


def main(args=None) -> int:
    configLogger(logger=log)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input sbix font")
    parser.add_argument("output", type=Path, help="output .ttf, .otf, or .woff2")
    parser.add_argument(
        "--ppem",
        type=int,
        help="sbix strike PPEM to convert (required; omit to list available values)",
    )
    parser.add_argument(
        "--gzip-docs",
        action="store_true",
        help="gzip each SVG document inside the font",
    )
    parser.add_argument(
        "--keep-sbix",
        action="store_true",
        help="retain the original sbix table alongside the new SVG table",
    )
    parser.add_argument(
        "--replace-svg",
        action="store_true",
        help="replace an existing SVG table",
    )
    options = parser.parse_args(args)

    if not options.input.is_file():
        parser.error(f"input font does not exist: {options.input}")
    suffix = options.output.suffix.lower()
    if suffix not in {".ttf", ".otf", ".woff2"}:
        parser.error("output extension must be .ttf, .otf, or .woff2")

    font = TTFont(options.input)
    try:
        if options.ppem is None:
            # Let the converter inspect the actual font and report its strikes.
            convert_sbix_to_otsvg(font, None)
        ppem, glyph_count = convert_sbix_to_otsvg(
            font,
            options.ppem,
            compress_documents=options.gzip_docs,
            keep_sbix=options.keep_sbix,
            replace_svg=options.replace_svg,
        )
        font.flavor = "woff2" if suffix == ".woff2" else None
        font.save(options.output)
    except (ImportError, KeyError, ValueError) as error:
        parser.error(str(error))
    finally:
        font.close()

    compression = "gzip" if options.gzip_docs else "plain"
    print(
        f"Wrote {options.output}: {glyph_count} PNG-backed SVG glyphs from "
        f"sbix ppem {ppem} ({compression} SVG documents)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
