from __future__ import print_function, absolute_import, division


class UnequalZipLengthsError(ValueError):
    pass


class IncompatibleGlyphsError(ValueError):

    def __init__(self, glyphs):
        assert len(glyphs) > 1
        self.glyphs = glyphs
        names = set(repr(g.name) for g in glyphs)
        if len(names) > 1:
            self.combined_name = "{%s}" % ", ".join(sorted(names))
        else:
            self.combined_name = names.pop()

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.combined_name)


class IncompatibleSegmentNumberError(IncompatibleGlyphsError):

    def __str__(self):
        return "Glyphs named %s have different number of segments" % (
            self.combined_name)


class IncompatibleSegmentTypesError(IncompatibleGlyphsError):

    def __init__(self, glyphs, segments):
        IncompatibleGlyphsError.__init__(self, glyphs)
        self.segments = segments

    def __str__(self):
        lines = []
        ndigits = len(str(max(self.segments)))
        for i, tags in sorted(self.segments.items()):
            lines.append("%s: (%s)" % (
                str(i).rjust(ndigits), ", ".join(repr(t) for t in tags)))
        return "Glyphs named %s have incompatible segment types:\n  %s" % (
            self.combined_name, "\n  ".join(lines))


class IncompatibleFontsError(ValueError):

    def __init__(self, glyph_errors):
        self.glyph_errors = glyph_errors

    def __str__(self):
        return "fonts contains incompatible glyphs: %s" % (
            ", ".join(repr(g) for g in sorted(self.glyph_errors.keys())))
