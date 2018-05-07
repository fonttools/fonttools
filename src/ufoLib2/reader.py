import attr
import os
from ufoLib2 import plistlib
from ufoLib2.constants import (
    DATA_DIRNAME, DEFAULT_GLYPHS_DIRNAME, FEATURES_FILENAME, FONTINFO_FILENAME,
    GROUPS_FILENAME, IMAGES_DIRNAME, KERNING_FILENAME, LAYERCONTENTS_FILENAME,
    LIB_FILENAME)
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
        self._getDirectoryListing(path, files, maxDepth=maxDepth)
        return files

    def _getDirectoryListing(self, path, files, depth=0, maxDepth=24):
        if depth > maxDepth:
            raise RuntimeError("maximum recursion depth %r exceeded" % maxDepth)
        try:
            listdir = os.listdir(path)
        except FileNotFoundError:
            return
        for fileName in listdir:
            f = os.path.join(path, fileName)
            if os.path.isdir(f):
                self._getDirectoryListing(
                    f, files, depth=depth+1, maxDepth=maxDepth)
            else:
                relPath = os.path.relpath(f, self._path)
                files.add(relPath)

    def getImageDirectoryListing(self):
        path = os.path.join(self._path, IMAGES_DIRNAME)
        files = set()
        try:
            listdir = os.listdir(path)
        except FileNotFoundError:
            return files
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
        if self._layerContents:
            assert self._layerContents[0][1] == DEFAULT_GLYPHS_DIRNAME
        return self._layerContents

    def getGlyphSet(self, dirName):
        path = os.path.join(self._path, dirName)
        return GlyphSet(path)

    # bin

    def readData(self, fileName):
        path = os.path.join(self._path, DATA_DIRNAME, fileName)
        try:
            with open(path, "rb") as file:
                data = file.read()
        except FileNotFoundError:
            data = None
        return data

    def readImage(self, fileName):
        path = os.path.join(self._path, IMAGES_DIRNAME, fileName)
        try:
            with open(path, "rb") as file:
                data = file.read()
        except FileNotFoundError:
            data = None
        return data

    # single reads

    def readFeatures(self):
        path = os.path.join(self._path, FEATURES_FILENAME)
        try:
            with open(path, "r") as file:
                text = file.read()
        except FileNotFoundError:
            text = ""
        return text

    def readGroups(self):
        path = os.path.join(self._path, GROUPS_FILENAME)
        try:
            with open(path, "rb") as file:
                data = plistlib.load(file)
        except FileNotFoundError:
            data = {}
        return data

    def readInfo(self):
        path = os.path.join(self._path, FONTINFO_FILENAME)
        try:
            with open(path, "rb") as file:
                data = plistlib.load(file)
        except FileNotFoundError:
            data = {}
        return data

    def readKerning(self):
        path = os.path.join(self._path, KERNING_FILENAME)
        try:
            with open(path, "rb") as file:
                data = plistlib.load(file)
        except FileNotFoundError:
            data = {}
        return data

    def readLib(self):
        path = os.path.join(self._path, LIB_FILENAME)
        try:
            with open(path, "rb") as file:
                data = plistlib.load(file)
        except FileNotFoundError:
            data = {}
        return data
