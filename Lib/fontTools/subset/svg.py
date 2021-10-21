import re
from itertools import groupby

from fontTools.subset.util import _add_method
from fontTools.misc import etree
from fontTools import ttLib


GID_RE = re.compile("^glyph(\d+)$")


XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def remap_glyph_ids(svg, glyph_index_map):
    id_map = {}
    href_elements = []
    for el in svg.iter("*"):
        # we'll rename these later
        if XLINK_HREF in el.attrib and el.attrib[XLINK_HREF].startswith("#"):
            href_elements.append(el)

        el_id = el.attrib.get("id")
        if el_id is None:
            continue
        m = GID_RE.match(el_id)
        if not m:
            continue
        old_index = int(m.group(1))
        new_index = glyph_index_map.get(old_index)
        if new_index is not None:
            if old_index == new_index:
                continue
            new_id = f"glyph{new_index}"
        else:
            # If the old id is missing, the element correspond to a glyph that was
            # excluded from the font's subset.
            # For now we keep it around, renamed to avoid clashes with the new GID
            # (though technically there could still be clashes even after we insert
            # a tilde at the beginning, e.g. '~glyphXXX' is still a valid id...).
            # TODO Figure out how to best prune the SVG document of unused elements.
            # https://github.com/fonttools/fonttools/issues/534
            new_id = f"~{el_id}"

        id_map[el_id] = new_id
        el.attrib["id"] = new_id

    if not id_map:
        return

    # update xlink:href="#..." that refer to the old id to point to the new one
    for el in href_elements:
        ref = el.attrib[XLINK_HREF]
        # we only care about local #fragment identifiers
        assert ref.startswith("#")
        old_id = ref[1:]
        if old_id in id_map:
            new_id = id_map[old_id]
            el.attrib[XLINK_HREF] = f"#{new_id}"


def ranges(ints):
    """Yield (min, max) ranges of consecutive integers from the input set"""
    sorted_ints = sorted(set(ints))
    # to group together consecutive ints, we use as 'key' the difference
    # between their index in the (sorted) list and themselves, which stays
    # the same for consecutive numbers
    for _key, group in groupby(enumerate(sorted_ints), lambda i: i[0] - i[1]):
        consecutive_ints = [v for _i, v in group]
        yield (consecutive_ints[0], consecutive_ints[-1])


@_add_method(ttLib.getTableClass("SVG "))
def subset_glyphs(self, s):
    # ordered list of glyph names (before subsetting)
    glyph_order = s.orig_glyph_order
    # map from glyph names to original glyph indices
    rev_orig_glyph_map = s.reverseOrigGlyphMap
    # map from original to new glyph indices (after subsetting)
    glyph_index_map = s.glyph_index_map

    new_docs = []
    for doc, start_gid, end_gid in self.docList:
        old_glyphs = {glyph_order[i] for i in range(start_gid, end_gid + 1)}
        new_glyphs = old_glyphs.intersection(s.glyphs)
        if not new_glyphs:
            # no intersection: we can drop the whole record
            continue

        # NOTE If new_glyphs != old_glyphs, there's only a partial intersection: i.e.
        # we'll likely end up with unused garbage until we figure out how to prune
        # the unused refereces from the SVG doc.

        # NOTE huge_tree=True disables security restrictions and support very deep trees
        # and very long text content. Without it I would get an error like this:
        # `lxml.etree.XMLSyntaxError: internal error: Huge input lookup`
        # when parsing noto-emoji-picosvg.svg from googlefonts/color-fonts.
        # This is lxml-only API, won't work with built-in ElementTree...
        svg = etree.fromstring(doc, parser=etree.XMLParser(huge_tree=True))

        remap_glyph_ids(svg, glyph_index_map)

        new_doc = etree.tostring(svg)

        new_gids = {glyph_index_map[rev_orig_glyph_map[g]] for g in new_glyphs}
        for start_gid, end_gid in ranges(new_gids):
            new_docs.append((new_doc, start_gid, end_gid))

    self.docList = new_docs

    return bool(self.docList)
