from __future__ import absolute_import, unicode_literals
import attr
import os
import errno
from io import open
from ufoLib2 import plistlib
from ufoLib2.constants import (
    DATA_DIRNAME,
    DEFAULT_GLYPHS_DIRNAME,
    FEATURES_FILENAME,
    FONTINFO_FILENAME,
    GROUPS_FILENAME,
    IMAGES_DIRNAME,
    KERNING_FILENAME,
    LAYERCONTENTS_FILENAME,
    LIB_FILENAME,
    DEFAULT_LAYER_NAME,
)
from ufoLib2.glyphSet import GlyphSet


@attr.s(slots=True)
class UFOReader(object):
    # TODO: we should probably take path-like objects, for zip etc. support.
    _path = attr.ib(type=str)
    _layerContents = attr.ib(init=False, repr=False, type=list)

    @property
    def path(self):
        return self._path

    def getDataDirectoryListing(self, maxDepth=24):
        path = os.path.join(self._path, DATA_DIRNAME)
        files = set()
        self._getDirectoryListing(path, files, DATA_DIRNAME, maxDepth=maxDepth)
        return files

    def _getDirectoryListing(self, path, files, base, depth=0, maxDepth=24):
        if depth > maxDepth:
            raise RuntimeError(
                "maximum recursion depth %r exceeded" % maxDepth
            )
        try:
            listdir = os.listdir(path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                return
            raise
        for fileName in listdir:
            f = os.path.join(path, fileName)
            if os.path.isdir(f):
                self._getDirectoryListing(
                    f, files, base, depth=depth + 1, maxDepth=maxDepth
                )
            else:
                relPath = os.path.relpath(f, os.path.join(self._path, base))
                files.add(relPath)

    def getImageDirectoryListing(self):
        path = os.path.join(self._path, IMAGES_DIRNAME)
        files = set()
        try:
            listdir = os.listdir(path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                return files
            raise
        for fileName in listdir:
            f = os.path.join(path, fileName)
            if os.path.isdir(f):
                continue
            files.add(fileName)
        return files

    # layers

    def getLayerContents(self):
        try:
            return self._layerContents
        except AttributeError:
            pass
        path = os.path.join(self._path, LAYERCONTENTS_FILENAME)
        with open(path, "rb") as file:
            self._layerContents = plistlib.load(file)
        for _, dirName in self._layerContents:
            if dirName == DEFAULT_GLYPHS_DIRNAME:
                break
        else:
            raise ValueError(
                "The default layer is not defined in layercontents.plist"
            )
        return self._layerContents

    def getDefaultLayerName(self):
        defaultLayerName = None
        publicDefaultDir = None
        for layerName, layerDirectory in self.getLayerContents():
            if layerDirectory == DEFAULT_GLYPHS_DIRNAME:
                defaultLayerName = layerName
            if layerName == DEFAULT_LAYER_NAME:
                publicDefaultDir = layerDirectory
        if (
            publicDefaultDir is not None
            and publicDefaultDir != DEFAULT_GLYPHS_DIRNAME
        ):
            raise ValueError(
                "'public.default' assigned to non-default directory: '%s'"
                % publicDefaultDir
            )
        # we checked it already
        assert defaultLayerName is not None, "default layer not found!"
        return defaultLayerName

    def getLayerNames(self):
        # for backward-compat with ufoLib API
        return [ln for ln, dn in self.getLayerContents()]

    def getGlyphSet(self, layerName=None):
        # for backward-compat with ufoLib API
        if layerName is None:
            dirName = DEFAULT_GLYPHS_DIRNAME
        else:
            for name, _ in self.getLayerContents():
                if layerName == name:
                    break
            else:
                raise ValueError(
                    'No glyphs directory is mapped to "%s".' % layerName
                )
        path = os.path.join(self._path, dirName)
        return GlyphSet(path)

    def iterGlyphSets(self):
        """Return an iterator over (layerName, GlyphSet) tuples."""
        for layerName, dirName in self.getLayerContents():
            yield layerName, GlyphSet(os.path.join(self._path, dirName))

    # bin

    def readData(self, fileName):
        path = os.path.join(self._path, DATA_DIRNAME, fileName)
        return self._readBin(path)

    def readImage(self, fileName):
        path = os.path.join(self._path, IMAGES_DIRNAME, fileName)
        return self._readBin(path)

    # single reads

    def readFeatures(self):
        path = os.path.join(self._path, FEATURES_FILENAME)
        return self._readText(path)

    def readGroups(self):
        path = os.path.join(self._path, GROUPS_FILENAME)
        return self._readPlist(path)

    def readInfo(self):
        path = os.path.join(self._path, FONTINFO_FILENAME)
        return self._readPlist(path)

    def readKerning(self):
        path = os.path.join(self._path, KERNING_FILENAME)
        kerningNested = self._readPlist(path)
        # flatten
        kerning = {}
        for left in kerningNested:
            for right in kerningNested[left]:
                kerning[left, right] = kerningNested[left][right]
        return kerning

    def readLib(self):
        path = os.path.join(self._path, LIB_FILENAME)
        return self._readPlist(path)

    # helpers

    @staticmethod
    def _readBin(path):
        try:
            with open(path, "rb") as file:
                return file.read()
        except (IOError, OSError) as e:
            if e.errno != errno.ENOENT:
                raise
            return None

    @staticmethod
    def _readText(path, encoding="utf-8"):
        try:
            with open(path, "r", encoding=encoding) as file:
                return file.read()
        except (IOError, OSError) as e:
            if e.errno != errno.ENOENT:
                raise
            return ""

    @staticmethod
    def _readPlist(path):
        try:
            with open(path, "rb") as file:
                return plistlib.load(file)
        except (IOError, OSError) as e:
            if e.errno != errno.ENOENT:
                raise
            return {}
