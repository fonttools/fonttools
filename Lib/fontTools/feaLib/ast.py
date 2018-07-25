from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.feaLib.error import FeatureLibError
from fontTools.misc.encodingTools import getEncoding
from collections import OrderedDict
import itertools

SHIFT = " " * 4

__all__ = [
    'AlternateSubstStatement',
    'Anchor',
    'AnchorDefinition',
    'AnonymousBlock',
    'AttachStatement',
    'BaseAxis',
    'Block',
    'BytesIO',
    'CVParametersNameStatement',
    'ChainContextPosStatement',
    'ChainContextSubstStatement',
    'CharacterStatement',
    'Comment',
    'CursivePosStatement',
    'Element',
    'Expression',
    'FeatureBlock',
    'FeatureFile',
    'FeatureLibError',
    'FeatureNameStatement',
    'FeatureReferenceStatement',
    'FontRevisionStatement',
    'GlyphClass',
    'GlyphClassDefStatement',
    'GlyphClassDefinition',
    'GlyphClassName',
    'GlyphName',
    'HheaField',
    'IgnorePosStatement',
    'IgnoreSubstStatement',
    'IncludeStatement',
    'LanguageStatement',
    'LanguageSystemStatement',
    'LigatureCaretByIndexStatement',
    'LigatureCaretByPosStatement',
    'LigatureSubstStatement',
    'LookupBlock',
    'LookupFlagStatement',
    'LookupReferenceStatement',
    'MarkBasePosStatement',
    'MarkClass',
    'MarkClassDefinition',
    'MarkClassName',
    'MarkLigPosStatement',
    'MarkMarkPosStatement',
    'MultipleSubstStatement',
    'NameRecord',
    'NestedBlock',
    'OS2Field',
    'OrderedDict',
    'PairPosStatement',
    'Py23Error',
    'ReverseChainSingleSubstStatement',
    'ScriptStatement',
    'SimpleNamespace',
    'SinglePosStatement',
    'SingleSubstStatement',
    'SizeParameters',
    'Statement',
    'StringIO',
    'SubtableStatement',
    'TableBlock',
    'Tag',
    'UnicodeIO',
    'ValueRecord',
    'ValueRecordDefinition',
    'VheaField',
]


def deviceToString(device):
    if device is None:
        return "<device NULL>"
    else:
        return "<device %s>" % ", ".join("%d %d" % t for t in device)


fea_keywords = set([
    "anchor", "anchordef", "anon", "anonymous",
    "by",
    "contour", "cursive",
    "device",
    "enum", "enumerate", "excludedflt", "exclude_dflt",
    "feature", "from",
    "ignore", "ignorebaseglyphs", "ignoreligatures", "ignoremarks",
    "include", "includedflt", "include_dflt",
    "language", "languagesystem", "lookup", "lookupflag",
    "mark", "markattachmenttype", "markclass",
    "nameid", "null",
    "parameters", "pos", "position",
    "required", "righttoleft", "reversesub", "rsub",
    "script", "sub", "substitute", "subtable",
    "table",
    "usemarkfilteringset", "useextension", "valuerecorddef"]
)


def asFea(g):
    if hasattr(g, 'asFea'):
        return g.asFea()
    elif isinstance(g, tuple) and len(g) == 2:
        return asFea(g[0]) + "-" + asFea(g[1])   # a range
    elif g.lower() in fea_keywords:
        return "\\" + g
    else:
        return g


class Element(object):

    def __init__(self, location=None):
        self.location = location

    def build(self, builder):
        pass

    def asFea(self, indent=""):
        raise NotImplementedError

    def __str__(self):
        return self.asFea()


class Statement(Element):
    pass


class Expression(Element):
    pass


class Comment(Element):
    def __init__(self, text, location=None):
        super(Comment, self).__init__(location)
        self.text = text

    def asFea(self, indent=""):
        return self.text


class GlyphName(Expression):
    """A single glyph name, such as cedilla."""
    def __init__(self, glyph, location=None):
        Expression.__init__(self, location)
        self.glyph = glyph

    def glyphSet(self):
        return (self.glyph,)

    def asFea(self, indent=""):
        return str(self.glyph)


class GlyphClass(Expression):
    """A glyph class, such as [acute cedilla grave]."""
    def __init__(self, glyphs=None, location=None):
        Expression.__init__(self, location)
        self.glyphs = glyphs if glyphs is not None else []
        self.original = []
        self.curr = 0

    def glyphSet(self):
        return tuple(self.glyphs)

    def asFea(self, indent=""):
        if len(self.original):
            if self.curr < len(self.glyphs):
                self.original.extend(self.glyphs[self.curr:])
                self.curr = len(self.glyphs)
            return "[" + " ".join(map(asFea, self.original)) + "]"
        else:
            return "[" + " ".join(map(asFea, self.glyphs)) + "]"

    def extend(self, glyphs):
        self.glyphs.extend(glyphs)

    def append(self, glyph):
        self.glyphs.append(glyph)

    def add_range(self, start, end, glyphs):
        if self.curr < len(self.glyphs):
            self.original.extend(self.glyphs[self.curr:])
        self.original.append((start, end))
        self.glyphs.extend(glyphs)
        self.curr = len(self.glyphs)

    def add_cid_range(self, start, end, glyphs):
        if self.curr < len(self.glyphs):
            self.original.extend(self.glyphs[self.curr:])
        self.original.append(("cid{:05d}".format(start), "cid{:05d}".format(end)))
        self.glyphs.extend(glyphs)
        self.curr = len(self.glyphs)

    def add_class(self, gc):
        if self.curr < len(self.glyphs):
            self.original.extend(self.glyphs[self.curr:])
        self.original.append(gc)
        self.glyphs.extend(gc.glyphSet())
        self.curr = len(self.glyphs)


class GlyphClassName(Expression):
    """A glyph class name, such as @FRENCH_MARKS."""
    def __init__(self, glyphclass, location=None):
        Expression.__init__(self, location)
        assert isinstance(glyphclass, GlyphClassDefinition)
        self.glyphclass = glyphclass

    def glyphSet(self):
        return tuple(self.glyphclass.glyphSet())

    def asFea(self, indent=""):
        return "@" + self.glyphclass.name


class MarkClassName(Expression):
    """A mark class name, such as @FRENCH_MARKS defined with markClass."""
    def __init__(self, markClass, location=None):
        Expression.__init__(self, location)
        assert isinstance(markClass, MarkClass)
        self.markClass = markClass

    def glyphSet(self):
        return self.markClass.glyphSet()

    def asFea(self, indent=""):
        return "@" + self.markClass.name


class AnonymousBlock(Statement):
    def __init__(self, tag, content, location=None):
        Statement.__init__(self, location)
        self.tag, self.content = tag, content

    def asFea(self, indent=""):
        res = "anon {} {{\n".format(self.tag)
        res += self.content
        res += "}} {};\n\n".format(self.tag)
        return res


class Block(Statement):
    def __init__(self, location=None):
        Statement.__init__(self, location)
        self.statements = []

    def build(self, builder):
        for s in self.statements:
            s.build(builder)

    def asFea(self, indent=""):
        indent += SHIFT
        return indent + ("\n" + indent).join(
            [s.asFea(indent=indent) for s in self.statements]) + "\n"


class FeatureFile(Block):
    def __init__(self):
        Block.__init__(self, location=None)
        self.markClasses = {}  # name --> ast.MarkClass

    def asFea(self, indent=""):
        return "\n".join(s.asFea(indent=indent) for s in self.statements)


class FeatureBlock(Block):
    def __init__(self, name, use_extension=False, location=None):
        Block.__init__(self, location)
        self.name, self.use_extension = name, use_extension

    def build(self, builder):
        # TODO(sascha): Handle use_extension.
        builder.start_feature(self.location, self.name)
        # language exclude_dflt statements modify builder.features_
        # limit them to this block with temporary builder.features_
        features = builder.features_
        builder.features_ = {}
        Block.build(self, builder)
        for key, value in builder.features_.items():
            features.setdefault(key, []).extend(value)
        builder.features_ = features
        builder.end_feature()

    def asFea(self, indent=""):
        res = indent + "feature %s {\n" % self.name.strip()
        res += Block.asFea(self, indent=indent)
        res += indent + "} %s;\n" % self.name.strip()
        return res


class NestedBlock(Block):
    def __init__(self, tag, block_name, location=None):
        Block.__init__(self, location)
        self.tag = tag
        self.block_name = block_name

    def build(self, builder):
        Block.build(self, builder)
        if self.block_name == "ParamUILabelNameID":
            builder.add_to_cv_num_named_params(self.tag)

    def asFea(self, indent=""):
        res = "{}{} {{\n".format(indent, self.block_name)
        res += Block.asFea(self, indent=indent)
        res += "{}}};\n".format(indent)
        return res


class LookupBlock(Block):
    def __init__(self, name, use_extension=False, location=None):
        Block.__init__(self, location)
        self.name, self.use_extension = name, use_extension

    def build(self, builder):
        # TODO(sascha): Handle use_extension.
        builder.start_lookup_block(self.location, self.name)
        Block.build(self, builder)
        builder.end_lookup_block()

    def asFea(self, indent=""):
        res = "lookup {} {{\n".format(self.name)
        res += Block.asFea(self, indent=indent)
        res += "{}}} {};\n".format(indent, self.name)
        return res


class TableBlock(Block):
    def __init__(self, name, location=None):
        Block.__init__(self, location)
        self.name = name

    def asFea(self, indent=""):
        res = "table {} {{\n".format(self.name.strip())
        res += super(TableBlock, self).asFea(indent=indent)
        res += "}} {};\n".format(self.name.strip())
        return res


class GlyphClassDefinition(Statement):
    """Example: @UPPERCASE = [A-Z];"""
    def __init__(self, name, glyphs, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.glyphs = glyphs

    def glyphSet(self):
        return tuple(self.glyphs.glyphSet())

    def asFea(self, indent=""):
        return "@" + self.name + " = " + self.glyphs.asFea() + ";"


class GlyphClassDefStatement(Statement):
    """Example: GlyphClassDef @UPPERCASE, [B], [C], [D];"""
    def __init__(self, baseGlyphs, markGlyphs, ligatureGlyphs,
                 componentGlyphs, location=None):
        Statement.__init__(self, location)
        self.baseGlyphs, self.markGlyphs = (baseGlyphs, markGlyphs)
        self.ligatureGlyphs = ligatureGlyphs
        self.componentGlyphs = componentGlyphs

    def build(self, builder):
        base = self.baseGlyphs.glyphSet() if self.baseGlyphs else tuple()
        liga = self.ligatureGlyphs.glyphSet() \
            if self.ligatureGlyphs else tuple()
        mark = self.markGlyphs.glyphSet() if self.markGlyphs else tuple()
        comp = (self.componentGlyphs.glyphSet()
                if self.componentGlyphs else tuple())
        builder.add_glyphClassDef(self.location, base, liga, mark, comp)

    def asFea(self, indent=""):
        return "GlyphClassDef {}, {}, {}, {};".format(
            self.baseGlyphs.asFea() if self.baseGlyphs else "",
            self.ligatureGlyphs.asFea() if self.ligatureGlyphs else "",
            self.markGlyphs.asFea() if self.markGlyphs else "",
            self.componentGlyphs.asFea() if self.componentGlyphs else "")


# While glyph classes can be defined only once, the feature file format
# allows expanding mark classes with multiple definitions, each using
# different glyphs and anchors. The following are two MarkClassDefinitions
# for the same MarkClass:
#     markClass [acute grave] <anchor 350 800> @FRENCH_ACCENTS;
#     markClass [cedilla] <anchor 350 -200> @FRENCH_ACCENTS;
class MarkClass(object):
    def __init__(self, name):
        self.name = name
        self.definitions = []
        self.glyphs = OrderedDict()  # glyph --> ast.MarkClassDefinitions

    def addDefinition(self, definition):
        assert isinstance(definition, MarkClassDefinition)
        self.definitions.append(definition)
        for glyph in definition.glyphSet():
            if glyph in self.glyphs:
                otherLoc = self.glyphs[glyph].location
                if otherLoc is None:
                    end = ""
                else:
                    end = " at %s:%d:%d" % (
                        otherLoc[0], otherLoc[1], otherLoc[2])
                raise FeatureLibError(
                    "Glyph %s already defined%s" % (glyph, end),
                    definition.location)
            self.glyphs[glyph] = definition

    def glyphSet(self):
        return tuple(self.glyphs.keys())

    def asFea(self, indent=""):
        res = "\n".join(d.asFea(indent=indent) for d in self.definitions)
        return res


class MarkClassDefinition(Statement):
    def __init__(self, markClass, anchor, glyphs, location=None):
        Statement.__init__(self, location)
        assert isinstance(markClass, MarkClass)
        assert isinstance(anchor, Anchor) and isinstance(glyphs, Expression)
        self.markClass, self.anchor, self.glyphs = markClass, anchor, glyphs

    def glyphSet(self):
        return self.glyphs.glyphSet()

    def asFea(self, indent=""):
        return "{}markClass {} {} @{};".format(
            indent, self.glyphs.asFea(), self.anchor.asFea(),
            self.markClass.name)


class AlternateSubstStatement(Statement):
    def __init__(self, prefix, glyph, suffix, replacement, location=None):
        Statement.__init__(self, location)
        self.prefix, self.glyph, self.suffix = (prefix, glyph, suffix)
        self.replacement = replacement

    def build(self, builder):
        glyph = self.glyph.glyphSet()
        assert len(glyph) == 1, glyph
        glyph = list(glyph)[0]
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        replacement = self.replacement.glyphSet()
        builder.add_alternate_subst(self.location, prefix, glyph, suffix,
                                    replacement)

    def asFea(self, indent=""):
        res = "sub "
        if len(self.prefix) or len(self.suffix):
            if len(self.prefix):
                res += " ".join(map(asFea, self.prefix)) + " "
            res += asFea(self.glyph) + "'"    # even though we really only use 1
            if len(self.suffix):
                res += " " + " ".join(map(asFea, self.suffix))
        else:
            res += asFea(self.glyph)
        res += " from "
        res += asFea(self.replacement)
        res += ";"
        return res


class Anchor(Expression):
    def __init__(self, x, y, name=None, contourpoint=None,
                 xDeviceTable=None, yDeviceTable=None, location=None):
        Expression.__init__(self, location)
        self.name = name
        self.x, self.y, self.contourpoint = x, y, contourpoint
        self.xDeviceTable, self.yDeviceTable = xDeviceTable, yDeviceTable

    def asFea(self, indent=""):
        if self.name is not None:
            return "<anchor {}>".format(self.name)
        res = "<anchor {} {}".format(self.x, self.y)
        if self.contourpoint:
            res += " contourpoint {}".format(self.contourpoint)
        if self.xDeviceTable or self.yDeviceTable:
            res += " "
            res += deviceToString(self.xDeviceTable)
            res += " "
            res += deviceToString(self.yDeviceTable)
        res += ">"
        return res


class AnchorDefinition(Statement):
    def __init__(self, name, x, y, contourpoint=None, location=None):
        Statement.__init__(self, location)
        self.name, self.x, self.y, self.contourpoint = name, x, y, contourpoint

    def asFea(self, indent=""):
        res = "anchorDef {} {}".format(self.x, self.y)
        if self.contourpoint:
            res += " contourpoint {}".format(self.contourpoint)
        res += " {};".format(self.name)
        return res


class AttachStatement(Statement):
    def __init__(self, glyphs, contourPoints, location=None):
        Statement.__init__(self, location)
        self.glyphs, self.contourPoints = (glyphs, contourPoints)

    def build(self, builder):
        glyphs = self.glyphs.glyphSet()
        builder.add_attach_points(self.location, glyphs, self.contourPoints)

    def asFea(self, indent=""):
        return "Attach {} {};".format(
            self.glyphs.asFea(), " ".join(str(c) for c in self.contourPoints))


class ChainContextPosStatement(Statement):
    def __init__(self, prefix, glyphs, suffix, lookups, location=None):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = prefix, glyphs, suffix
        self.lookups = lookups

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        glyphs = [g.glyphSet() for g in self.glyphs]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_chain_context_pos(
            self.location, prefix, glyphs, suffix, self.lookups)

    def asFea(self, indent=""):
        res = "pos "
        if len(self.prefix) or len(self.suffix) or any([x is not None for x in self.lookups]):
            if len(self.prefix):
                res += " ".join(g.asFea() for g in self.prefix) + " "
            for i, g in enumerate(self.glyphs):
                res += g.asFea() + "'"
                if self.lookups[i] is not None:
                    res += " lookup " + self.lookups[i].name
                if i < len(self.glyphs) - 1:
                    res += " "
            if len(self.suffix):
                res += " " + " ".join(map(asFea, self.suffix))
        else:
            res += " ".join(map(asFea, self.glyph))
        res += ";"
        return res


class ChainContextSubstStatement(Statement):
    def __init__(self, prefix, glyphs, suffix, lookups, location=None):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = prefix, glyphs, suffix
        self.lookups = lookups

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        glyphs = [g.glyphSet() for g in self.glyphs]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_chain_context_subst(
            self.location, prefix, glyphs, suffix, self.lookups)

    def asFea(self, indent=""):
        res = "sub "
        if len(self.prefix) or len(self.suffix) or any([x is not None for x in self.lookups]):
            if len(self.prefix):
                res += " ".join(g.asFea() for g in self.prefix) + " "
            for i, g in enumerate(self.glyphs):
                res += g.asFea() + "'"
                if self.lookups[i] is not None:
                    res += " lookup " + self.lookups[i].name
                if i < len(self.glyphs) - 1:
                    res += " "
            if len(self.suffix):
                res += " " + " ".join(map(asFea, self.suffix))
        else:
            res += " ".join(map(asFea, self.glyph))
        res += ";"
        return res


class CursivePosStatement(Statement):
    def __init__(self, glyphclass, entryAnchor, exitAnchor, location=None):
        Statement.__init__(self, location)
        self.glyphclass = glyphclass
        self.entryAnchor, self.exitAnchor = entryAnchor, exitAnchor

    def build(self, builder):
        builder.add_cursive_pos(
            self.location, self.glyphclass.glyphSet(), self.entryAnchor, self.exitAnchor)

    def asFea(self, indent=""):
        entry = self.entryAnchor.asFea() if self.entryAnchor else "<anchor NULL>"
        exit = self.exitAnchor.asFea() if self.exitAnchor else "<anchor NULL>"
        return "pos cursive {} {} {};".format(self.glyphclass.asFea(), entry, exit)


class FeatureReferenceStatement(Statement):
    """Example: feature salt;"""
    def __init__(self, featureName, location=None):
        Statement.__init__(self, location)
        self.location, self.featureName = (location, featureName)

    def build(self, builder):
        builder.add_feature_reference(self.location, self.featureName)

    def asFea(self, indent=""):
        return "feature {};".format(self.featureName)


class IgnorePosStatement(Statement):
    def __init__(self, chainContexts, location=None):
        Statement.__init__(self, location)
        self.chainContexts = chainContexts

    def build(self, builder):
        for prefix, glyphs, suffix in self.chainContexts:
            prefix = [p.glyphSet() for p in prefix]
            glyphs = [g.glyphSet() for g in glyphs]
            suffix = [s.glyphSet() for s in suffix]
            builder.add_chain_context_pos(
                self.location, prefix, glyphs, suffix, [])

    def asFea(self, indent=""):
        contexts = []
        for prefix, glyphs, suffix in self.chainContexts:
            res = ""
            if len(prefix) or len(suffix):
                if len(prefix):
                    res += " ".join(map(asFea, prefix)) + " "
                res += " ".join(g.asFea() + "'" for g in glyphs)
                if len(suffix):
                    res += " " + " ".join(map(asFea, suffix))
            else:
                res += " ".join(map(asFea, glyphs))
            contexts.append(res)
        return "ignore pos " + ", ".join(contexts) + ";"


class IgnoreSubstStatement(Statement):
    def __init__(self, chainContexts, location=None):
        Statement.__init__(self, location)
        self.chainContexts = chainContexts

    def build(self, builder):
        for prefix, glyphs, suffix in self.chainContexts:
            prefix = [p.glyphSet() for p in prefix]
            glyphs = [g.glyphSet() for g in glyphs]
            suffix = [s.glyphSet() for s in suffix]
            builder.add_chain_context_subst(
                self.location, prefix, glyphs, suffix, [])

    def asFea(self, indent=""):
        contexts = []
        for prefix, glyphs, suffix in self.chainContexts:
            res = ""
            if len(prefix) or len(suffix):
                if len(prefix):
                    res += " ".join(map(asFea, prefix)) + " "
                res += " ".join(g.asFea() + "'" for g in glyphs)
                if len(suffix):
                    res += " " + " ".join(map(asFea, suffix))
            else:
                res += " ".join(map(asFea, glyphs))
            contexts.append(res)
        return "ignore sub " + ", ".join(contexts) + ";"


class IncludeStatement(Statement):
    def __init__(self, filename, location=None):
        super(IncludeStatement, self).__init__(location)
        self.filename = filename

    def build(self):
        # TODO: consider lazy-loading the including parser/lexer?
        raise FeatureLibError(
            "Building an include statement is not implemented yet. "
            "Instead, use Parser(..., followIncludes=True) for building.",
            self.location)

    def asFea(self, indent=""):
        return indent + "include(%s);" % self.filename


class LanguageStatement(Statement):
    def __init__(self, language, include_default=True, required=False,
                 location=None):
        Statement.__init__(self, location)
        assert(len(language) == 4)
        self.language = language
        self.include_default = include_default
        self.required = required

    def build(self, builder):
        builder.set_language(location=self.location, language=self.language,
                             include_default=self.include_default,
                             required=self.required)

    def asFea(self, indent=""):
        res = "language {}".format(self.language.strip())
        if not self.include_default:
            res += " exclude_dflt"
        if self.required:
            res += " required"
        res += ";"
        return res


class LanguageSystemStatement(Statement):
    def __init__(self, script, language, location=None):
        Statement.__init__(self, location)
        self.script, self.language = (script, language)

    def build(self, builder):
        builder.add_language_system(self.location, self.script, self.language)

    def asFea(self, indent=""):
        return "languagesystem {} {};".format(self.script, self.language.strip())


class FontRevisionStatement(Statement):
    def __init__(self, revision, location=None):
        Statement.__init__(self, location)
        self.revision = revision

    def build(self, builder):
        builder.set_font_revision(self.location, self.revision)

    def asFea(self, indent=""):
        return "FontRevision {:.3f};".format(self.revision)


class LigatureCaretByIndexStatement(Statement):
    def __init__(self, glyphs, carets, location=None):
        Statement.__init__(self, location)
        self.glyphs, self.carets = (glyphs, carets)

    def build(self, builder):
        glyphs = self.glyphs.glyphSet()
        builder.add_ligatureCaretByIndex_(self.location, glyphs, set(self.carets))

    def asFea(self, indent=""):
        return "LigatureCaretByIndex {} {};".format(
            self.glyphs.asFea(), " ".join(str(x) for x in self.carets))


class LigatureCaretByPosStatement(Statement):
    def __init__(self, glyphs, carets, location=None):
        Statement.__init__(self, location)
        self.glyphs, self.carets = (glyphs, carets)

    def build(self, builder):
        glyphs = self.glyphs.glyphSet()
        builder.add_ligatureCaretByPos_(self.location, glyphs, set(self.carets))

    def asFea(self, indent=""):
        return "LigatureCaretByPos {} {};".format(
            self.glyphs.asFea(), " ".join(str(x) for x in self.carets))


class LigatureSubstStatement(Statement):
    def __init__(self, prefix, glyphs, suffix, replacement,
                 forceChain, location=None):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = (prefix, glyphs, suffix)
        self.replacement, self.forceChain = replacement, forceChain

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        glyphs = [g.glyphSet() for g in self.glyphs]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_ligature_subst(
            self.location, prefix, glyphs, suffix, self.replacement,
            self.forceChain)

    def asFea(self, indent=""):
        res = "sub "
        if len(self.prefix) or len(self.suffix) or self.forceChain:
            if len(self.prefix):
                res += " ".join(g.asFea() for g in self.prefix) + " "
            res += " ".join(g.asFea() + "'" for g in self.glyphs)
            if len(self.suffix):
                res += " " + " ".join(g.asFea() for g in self.suffix)
        else:
            res += " ".join(g.asFea() for g in self.glyphs)
        res += " by "
        res += asFea(self.replacement)
        res += ";"
        return res


class LookupFlagStatement(Statement):
    def __init__(self, value=0, markAttachment=None, markFilteringSet=None,
                 location=None):
        Statement.__init__(self, location)
        self.value = value
        self.markAttachment = markAttachment
        self.markFilteringSet = markFilteringSet

    def build(self, builder):
        markAttach = None
        if self.markAttachment is not None:
            markAttach = self.markAttachment.glyphSet()
        markFilter = None
        if self.markFilteringSet is not None:
            markFilter = self.markFilteringSet.glyphSet()
        builder.set_lookup_flag(self.location, self.value,
                                markAttach, markFilter)

    def asFea(self, indent=""):
        res = "lookupflag"
        flags = ["RightToLeft", "IgnoreBaseGlyphs", "IgnoreLigatures", "IgnoreMarks"]
        curr = 1
        for i in range(len(flags)):
            if self.value & curr != 0:
                res += " " + flags[i]
            curr = curr << 1
        if self.markAttachment is not None:
            res += " MarkAttachmentType {}".format(self.markAttachment.asFea())
        if self.markFilteringSet is not None:
            res += " UseMarkFilteringSet {}".format(self.markFilteringSet.asFea())
        res += ";"
        return res


class LookupReferenceStatement(Statement):
    def __init__(self, lookup, location=None):
        Statement.__init__(self, location)
        self.location, self.lookup = (location, lookup)

    def build(self, builder):
        builder.add_lookup_call(self.lookup.name)

    def asFea(self, indent=""):
        return "lookup {};".format(self.lookup.name)


class MarkBasePosStatement(Statement):
    def __init__(self, base, marks, location=None):
        Statement.__init__(self, location)
        self.base, self.marks = base, marks

    def build(self, builder):
        builder.add_mark_base_pos(self.location, self.base.glyphSet(), self.marks)

    def asFea(self, indent=""):
        res = "pos base {}".format(self.base.asFea())
        for a, m in self.marks:
            res += " {} mark @{}".format(a.asFea(), m.name)
        res += ";"
        return res


class MarkLigPosStatement(Statement):
    def __init__(self, ligatures, marks, location=None):
        Statement.__init__(self, location)
        self.ligatures, self.marks = ligatures, marks

    def build(self, builder):
        builder.add_mark_lig_pos(self.location, self.ligatures.glyphSet(), self.marks)

    def asFea(self, indent=""):
        res = "pos ligature {}".format(self.ligatures.asFea())
        ligs = []
        for l in self.marks:
            temp = ""
            if l is None or not len(l):
                temp = " <anchor NULL>"
            else:
                for a, m in l:
                    temp += " {} mark @{}".format(a.asFea(), m.name)
            ligs.append(temp)
        res += ("\n" + indent + SHIFT + "ligComponent").join(ligs)
        res += ";"
        return res


class MarkMarkPosStatement(Statement):
    def __init__(self, baseMarks, marks, location=None):
        Statement.__init__(self, location)
        self.baseMarks, self.marks = baseMarks, marks

    def build(self, builder):
        builder.add_mark_mark_pos(self.location, self.baseMarks.glyphSet(), self.marks)

    def asFea(self, indent=""):
        res = "pos mark {}".format(self.baseMarks.asFea())
        for a, m in self.marks:
            res += " {} mark @{}".format(a.asFea(), m.name)
        res += ";"
        return res


class MultipleSubstStatement(Statement):
    def __init__(self, prefix, glyph, suffix, replacement, location=None):
        Statement.__init__(self, location)
        self.prefix, self.glyph, self.suffix = prefix, glyph, suffix
        self.replacement = replacement

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_multiple_subst(
            self.location, prefix, self.glyph, suffix, self.replacement)

    def asFea(self, indent=""):
        res = "sub "
        if len(self.prefix) or len(self.suffix):
            if len(self.prefix):
                res += " ".join(map(asFea, self.prefix)) + " "
            res += asFea(self.glyph) + "'"
            if len(self.suffix):
                res += " " + " ".join(map(asFea, self.suffix))
        else:
            res += asFea(self.glyph)
        res += " by "
        res += " ".join(map(asFea, self.replacement))
        res += ";"
        return res


class PairPosStatement(Statement):
    def __init__(self, glyphs1, valuerecord1, glyphs2, valuerecord2,
                 enumerated=False, location=None):
        Statement.__init__(self, location)
        self.enumerated = enumerated
        self.glyphs1, self.valuerecord1 = glyphs1, valuerecord1
        self.glyphs2, self.valuerecord2 = glyphs2, valuerecord2

    def build(self, builder):
        if self.enumerated:
            g = [self.glyphs1.glyphSet(), self.glyphs2.glyphSet()]
            for glyph1, glyph2 in itertools.product(*g):
                builder.add_specific_pair_pos(
                    self.location, glyph1, self.valuerecord1,
                    glyph2, self.valuerecord2)
            return

        is_specific = (isinstance(self.glyphs1, GlyphName) and
                       isinstance(self.glyphs2, GlyphName))
        if is_specific:
            builder.add_specific_pair_pos(
                self.location, self.glyphs1.glyph, self.valuerecord1,
                self.glyphs2.glyph, self.valuerecord2)
        else:
            builder.add_class_pair_pos(
                self.location, self.glyphs1.glyphSet(), self.valuerecord1,
                self.glyphs2.glyphSet(), self.valuerecord2)

    def asFea(self, indent=""):
        res = "enum " if self.enumerated else ""
        if self.valuerecord2:
            res += "pos {} {} {} {};".format(
                self.glyphs1.asFea(), self.valuerecord1.makeString(),
                self.glyphs2.asFea(), self.valuerecord2.makeString())
        else:
            res += "pos {} {} {};".format(
                self.glyphs1.asFea(), self.glyphs2.asFea(),
                self.valuerecord1.makeString())
        return res


class ReverseChainSingleSubstStatement(Statement):
    def __init__(self, old_prefix, old_suffix, glyphs, replacements,
                 location=None):
        Statement.__init__(self, location)
        self.old_prefix, self.old_suffix = old_prefix, old_suffix
        self.glyphs = glyphs
        self.replacements = replacements

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.old_prefix]
        suffix = [s.glyphSet() for s in self.old_suffix]
        originals = self.glyphs[0].glyphSet()
        replaces = self.replacements[0].glyphSet()
        if len(replaces) == 1:
            replaces = replaces * len(originals)
        builder.add_reverse_chain_single_subst(
            self.location, prefix, suffix, dict(zip(originals, replaces)))

    def asFea(self, indent=""):
        res = "rsub "
        if len(self.old_prefix) or len(self.old_suffix):
            if len(self.old_prefix):
                res += " ".join(asFea(g) for g in self.old_prefix) + " "
            res += " ".join(asFea(g) + "'" for g in self.glyphs)
            if len(self.old_suffix):
                res += " " + " ".join(asFea(g) for g in self.old_suffix)
        else:
            res += " ".join(map(asFea, self.glyphs))
        res += " by {};".format(" ".join(asFea(g) for g in self.replacements))
        return res


class SingleSubstStatement(Statement):
    def __init__(self, glyphs, replace, prefix, suffix, forceChain,
                 location=None):
        Statement.__init__(self, location)
        self.prefix, self.suffix = prefix, suffix
        self.forceChain = forceChain
        self.glyphs = glyphs
        self.replacements = replace

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        originals = self.glyphs[0].glyphSet()
        replaces = self.replacements[0].glyphSet()
        if len(replaces) == 1:
            replaces = replaces * len(originals)
        builder.add_single_subst(self.location, prefix, suffix,
                                 OrderedDict(zip(originals, replaces)),
                                 self.forceChain)

    def asFea(self, indent=""):
        res = "sub "
        if len(self.prefix) or len(self.suffix) or self.forceChain:
            if len(self.prefix):
                res += " ".join(asFea(g) for g in self.prefix) + " "
            res += " ".join(asFea(g) + "'" for g in self.glyphs)
            if len(self.suffix):
                res += " " + " ".join(asFea(g) for g in self.suffix)
        else:
            res += " ".join(asFea(g) for g in self.glyphs)
        res += " by {};".format(" ".join(asFea(g) for g in self.replacements))
        return res


class ScriptStatement(Statement):
    def __init__(self, script, location=None):
        Statement.__init__(self, location)
        self.script = script

    def build(self, builder):
        builder.set_script(self.location, self.script)

    def asFea(self, indent=""):
        return "script {};".format(self.script.strip())


class SinglePosStatement(Statement):
    def __init__(self, pos, prefix, suffix, forceChain, location=None):
        Statement.__init__(self, location)
        self.pos, self.prefix, self.suffix = pos, prefix, suffix
        self.forceChain = forceChain

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        pos = [(g.glyphSet(), value) for g, value in self.pos]
        builder.add_single_pos(self.location, prefix, suffix,
                               pos, self.forceChain)

    def asFea(self, indent=""):
        res = "pos "
        if len(self.prefix) or len(self.suffix) or self.forceChain:
            if len(self.prefix):
                res += " ".join(map(asFea, self.prefix)) + " "
            res += " ".join([asFea(x[0]) + "'" + (
                (" " + x[1].makeString()) if x[1] else "") for x in self.pos])
            if len(self.suffix):
                res += " " + " ".join(map(asFea, self.suffix))
        else:
            res += " ".join([asFea(x[0]) + " " +
                             (x[1].makeString() if x[1] else "") for x in self.pos])
        res += ";"
        return res


class SubtableStatement(Statement):
    def __init__(self, location=None):
        Statement.__init__(self, location)

    def build(self, builder):
        builder.add_subtable_break(self.location)

    def asFea(self, indent=""):
        return indent + "subtable;"


class ValueRecord(Expression):
    def __init__(self, xPlacement=None, yPlacement=None,
                 xAdvance=None, yAdvance=None,
                 xPlaDevice=None, yPlaDevice=None,
                 xAdvDevice=None, yAdvDevice=None,
                 vertical=False, location=None):
        Expression.__init__(self, location)
        self.xPlacement, self.yPlacement = (xPlacement, yPlacement)
        self.xAdvance, self.yAdvance = (xAdvance, yAdvance)
        self.xPlaDevice, self.yPlaDevice = (xPlaDevice, yPlaDevice)
        self.xAdvDevice, self.yAdvDevice = (xAdvDevice, yAdvDevice)
        self.vertical = vertical

    def __eq__(self, other):
        return (self.xPlacement == other.xPlacement and
                self.yPlacement == other.yPlacement and
                self.xAdvance == other.xAdvance and
                self.yAdvance == other.yAdvance and
                self.xPlaDevice == other.xPlaDevice and
                self.xAdvDevice == other.xAdvDevice)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return (hash(self.xPlacement) ^ hash(self.yPlacement) ^
                hash(self.xAdvance) ^ hash(self.yAdvance) ^
                hash(self.xPlaDevice) ^ hash(self.yPlaDevice) ^
                hash(self.xAdvDevice) ^ hash(self.yAdvDevice))

    def makeString(self, vertical=None):
        x, y = self.xPlacement, self.yPlacement
        xAdvance, yAdvance = self.xAdvance, self.yAdvance
        xPlaDevice, yPlaDevice = self.xPlaDevice, self.yPlaDevice
        xAdvDevice, yAdvDevice = self.xAdvDevice, self.yAdvDevice
        if vertical is None:
            vertical = self.vertical

        # Try format A, if possible.
        if x is None and y is None:
            if xAdvance is None and vertical:
                return str(yAdvance)
            elif yAdvance is None and not vertical:
                return str(xAdvance)

        # Try format B, if possible.
        if (xPlaDevice is None and yPlaDevice is None and
                xAdvDevice is None and yAdvDevice is None):
            return "<%s %s %s %s>" % (x, y, xAdvance, yAdvance)

        # Last resort is format C.
        return "<%s %s %s %s %s %s %s %s>" % (
            x, y, xAdvance, yAdvance,
            deviceToString(xPlaDevice), deviceToString(yPlaDevice),
            deviceToString(xAdvDevice), deviceToString(yAdvDevice))


class ValueRecordDefinition(Statement):
    def __init__(self, name, value, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.value = value

    def asFea(self, indent=""):
        return "valueRecordDef {} {};".format(self.value.asFea(), self.name)


def simplify_name_attributes(pid, eid, lid):
    if pid == 3 and eid == 1 and lid == 1033:
        return ""
    elif pid == 1 and eid == 0 and lid == 0:
        return "1"
    else:
        return "{} {} {}".format(pid, eid, lid)


class NameRecord(Statement):
    def __init__(self, nameID, platformID, platEncID, langID, string,
                 location=None):
        Statement.__init__(self, location)
        self.nameID = nameID
        self.platformID = platformID
        self.platEncID = platEncID
        self.langID = langID
        self.string = string

    def build(self, builder):
        builder.add_name_record(
            self.location, self.nameID, self.platformID,
            self.platEncID, self.langID, self.string)

    def asFea(self, indent=""):
        def escape(c, escape_pattern):
            # Also escape U+0022 QUOTATION MARK and U+005C REVERSE SOLIDUS
            if c >= 0x20 and c <= 0x7E and c not in (0x22, 0x5C):
                return unichr(c)
            else:
                return escape_pattern % c
        encoding = getEncoding(self.platformID, self.platEncID, self.langID)
        if encoding is None:
            raise FeatureLibError("Unsupported encoding", self.location)
        s = tobytes(self.string, encoding=encoding)
        if encoding == "utf_16_be":
            escaped_string = "".join([
                escape(byteord(s[i]) * 256 + byteord(s[i + 1]), r"\%04x")
                for i in range(0, len(s), 2)])
        else:
            escaped_string = "".join([escape(byteord(b), r"\%02x") for b in s])
        plat = simplify_name_attributes(
            self.platformID, self.platEncID, self.langID)
        if plat != "":
            plat += " "
        return "nameid {} {}\"{}\";".format(self.nameID, plat, escaped_string)


class FeatureNameStatement(NameRecord):
    def build(self, builder):
        NameRecord.build(self, builder)
        builder.add_featureName(self.nameID)

    def asFea(self, indent=""):
        if self.nameID == "size":
            tag = "sizemenuname"
        else:
            tag = "name"
        plat = simplify_name_attributes(self.platformID, self.platEncID, self.langID)
        if plat != "":
            plat += " "
        return "{} {}\"{}\";".format(tag, plat, self.string)


class SizeParameters(Statement):
    def __init__(self, DesignSize, SubfamilyID, RangeStart, RangeEnd,
                 location=None):
        Statement.__init__(self, location)
        self.DesignSize = DesignSize
        self.SubfamilyID = SubfamilyID
        self.RangeStart = RangeStart
        self.RangeEnd = RangeEnd

    def build(self, builder):
        builder.set_size_parameters(self.location, self.DesignSize,
                                    self.SubfamilyID, self.RangeStart, self.RangeEnd)

    def asFea(self, indent=""):
        res = "parameters {:.1f} {}".format(self.DesignSize, self.SubfamilyID)
        if self.RangeStart != 0 or self.RangeEnd != 0:
            res += " {} {}".format(int(self.RangeStart * 10), int(self.RangeEnd * 10))
        return res + ";"


class CVParametersNameStatement(NameRecord):
    def __init__(self, nameID, platformID, platEncID, langID, string,
                 block_name, location=None):
        NameRecord.__init__(self, nameID, platformID, platEncID, langID,
                            string, location=location)
        self.block_name = block_name

    def build(self, builder):
        item = ""
        if self.block_name == "ParamUILabelNameID":
            item = "_{}".format(builder.cv_num_named_params_.get(self.nameID, 0))
        builder.add_cv_parameter(self.nameID)
        self.nameID = (self.nameID, self.block_name + item)
        NameRecord.build(self, builder)

    def asFea(self, indent=""):
        plat = simplify_name_attributes(self.platformID, self.platEncID,
                                        self.langID)
        if plat != "":
            plat += " "
        return "name {}\"{}\";".format(plat, self.string)


class CharacterStatement(Statement):
    """
    Statement used in cvParameters blocks of Character Variant features (cvXX).
    The Unicode value may be written with either decimal or hexadecimal
    notation. The value must be preceded by '0x' if it is a hexadecimal value.
    The largest Unicode value allowed is 0xFFFFFF.
    """
    def __init__(self, character, tag, location=None):
        Statement.__init__(self, location)
        self.character = character
        self.tag = tag

    def build(self, builder):
        builder.add_cv_character(self.character, self.tag)

    def asFea(self, indent=""):
        return "Character {:#x};".format(self.character)


class BaseAxis(Statement):
    def __init__(self, bases, scripts, vertical, location=None):
        Statement.__init__(self, location)
        self.bases = bases
        self.scripts = scripts
        self.vertical = vertical

    def build(self, builder):
        builder.set_base_axis(self.bases, self.scripts, self.vertical)

    def asFea(self, indent=""):
        direction = "Vert" if self.vertical else "Horiz"
        scripts = ["{} {} {}".format(a[0], a[1], " ".join(map(str, a[2]))) for a in self.scripts]
        return "{}Axis.BaseTagList {};\n{}{}Axis.BaseScriptList {};".format(
            direction, " ".join(self.bases), indent, direction, ", ".join(scripts))


class OS2Field(Statement):
    def __init__(self, key, value, location=None):
        Statement.__init__(self, location)
        self.key = key
        self.value = value

    def build(self, builder):
        builder.add_os2_field(self.key, self.value)

    def asFea(self, indent=""):
        def intarr2str(x):
            return " ".join(map(str, x))
        numbers = ("FSType", "TypoAscender", "TypoDescender", "TypoLineGap",
                   "winAscent", "winDescent", "XHeight", "CapHeight",
                   "WeightClass", "WidthClass", "LowerOpSize", "UpperOpSize")
        ranges = ("UnicodeRange", "CodePageRange")
        keywords = dict([(x.lower(), [x, str]) for x in numbers])
        keywords.update([(x.lower(), [x, intarr2str]) for x in ranges])
        keywords["panose"] = ["Panose", intarr2str]
        keywords["vendor"] = ["Vendor", lambda y: '"{}"'.format(y)]
        if self.key in keywords:
            return "{} {};".format(keywords[self.key][0], keywords[self.key][1](self.value))
        return ""   # should raise exception


class HheaField(Statement):
    def __init__(self, key, value, location=None):
        Statement.__init__(self, location)
        self.key = key
        self.value = value

    def build(self, builder):
        builder.add_hhea_field(self.key, self.value)

    def asFea(self, indent=""):
        fields = ("CaretOffset", "Ascender", "Descender", "LineGap")
        keywords = dict([(x.lower(), x) for x in fields])
        return "{} {};".format(keywords[self.key], self.value)


class VheaField(Statement):
    def __init__(self, key, value, location=None):
        Statement.__init__(self, location)
        self.key = key
        self.value = value

    def build(self, builder):
        builder.add_vhea_field(self.key, self.value)

    def asFea(self, indent=""):
        fields = ("VertTypoAscender", "VertTypoDescender", "VertTypoLineGap")
        keywords = dict([(x.lower(), x) for x in fields])
        return "{} {};".format(keywords[self.key], self.value)
