import attr
from typing import Optional
from ufoLib2.objects.glyph import Glyph, GlyphClasses
from ufoLib2.reader import GlyphSet
from ufoLib2.constants import DEFAULT_LAYER_NAME


@attr.s(slots=True)
class Layer(object):
    _name = attr.ib(default=DEFAULT_LAYER_NAME, type=str)
    _glyphSet = attr.ib(default=None, repr=False, type=GlyphSet)
    _glyphs = attr.ib(
        default=attr.Factory(dict), init=False, repr=False, type=dict
    )
    _keys = attr.ib(init=False, repr=False, type=set)
    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, repr=False, type=set
    )

    color = attr.ib(default=None, init=False, repr=False, type=Optional[str])
    lib = attr.ib(
        default=attr.Factory(dict), init=False, repr=False, type=dict
    )

    def __attrs_post_init__(self):
        # TODO: this could be done lazily
        if self._glyphSet is not None:
            keys = set(self._glyphSet.keys())
        else:
            keys = set()
        self._keys = keys

    def __contains__(self, name):
        return name in self._keys

    def __delitem__(self, name):
        if name not in self._keys:
            raise KeyError("name %r is not in layer" % name)
        self._delete(name)

    def __getitem__(self, name):
        if name not in self._glyphs:
            self.loadGlyph(name)
        return self._glyphs[name]

    def __iter__(self):
        for name in self._keys:
            yield self[name]

    def __len__(self):
        return len(self._keys)

    def _delete(self, name):
        # if the glyph is loaded, delete it
        if name in self._glyphs:
            del self._glyphs[name]
        # if the glyph is on disk, schedule for removal
        if self._glyphSet is not None and name in self._glyphSet:
            self._scheduledForDeletion.add(name)
        self._keys.remove(name)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            pass
        return default

    def keys(self):
        return set(self._keys)

    @property
    def name(self):
        return self._name

    def addGlyph(self, glyph):
        if glyph.name in self._keys:
            raise KeyError("glyph %r already exists" % glyph.name)
        self._glyphs[glyph.name] = glyph
        self._keys.add(glyph.name)
        if glyph.name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(glyph.name)

    def loadGlyph(self, name):
        if (
            self._glyphSet is None
            or name not in self._glyphSet
            or name in self._scheduledForDeletion
        ):
            raise KeyError("name %r not in layer" % name)
        glyph = self._glyphSet.readGlyph(name, GlyphClasses)
        self._glyphs[name] = glyph

    def newGlyph(self, name):
        if name in self._keys:
            raise KeyError("glyph %r already exists" % name)
        self._glyphs[name] = glyph = Glyph(name)
        self._keys.add(name)
        if name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(name)
        return glyph

    def renameGlyph(self, name, newName, overwrite=False):
        if name == newName:
            return
        if not overwrite and newName in self._keys:
            raise KeyError("target glyph %r already exists" % newName)
        # load-get and delete
        glyph = self[name]
        self._delete(name)
        # add new
        self._glyphs[newName] = glyph
        self._keys.add(newName)
        if newName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(newName)
        # set name
        glyph._name = newName

    def save(self, glyphSet, saveAs=False):
        if saveAs:
            glyphs = self
        else:
            glyphs = self._glyphs
            for name in self._scheduledForDeletion:
                if name in glyphSet:
                    glyphSet.deleteGlyph(name)
        for glyph in glyphs:
            glyphSet.writeGlyph(glyph)
        glyphSet.writeContents()
        self._glyphSet = glyphSet
        self._scheduledForDeletion = set()
