from fontTools.subset.util import _add_method
from fontTools import ttLib


@_add_method(ttLib.getTableClass("SVG "))
def subset_glyphs(self, s):
    return True  # XXX
