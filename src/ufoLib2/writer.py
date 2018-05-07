import attr
from fontTools.misc.filenames import userNameToFileName
import os
import plistlib
import shutil
from ufoLib2.constants import (
    DATA_DIRNAME, DEFAULT_GLYPHS_DIRNAME, FEATURES_FILENAME, FONTINFO_FILENAME,
    GROUPS_FILENAME, KERNING_FILENAME, IMAGES_DIRNAME, LAYERCONTENTS_FILENAME,
    LIB_FILENAME, METAINFO_FILENAME)
from ufoLib2.glyphSet import GlyphSet


@attr.s(slots=True)
class UFOWriter(object):
    # TODO: we should probably take path-like objects, for zip etc. support.
    _path = attr.ib(type=str)
    _layerContents = attr.ib(default=attr.Factory(dict), init=False, repr=False, type=list)

    def __attrs_post_init__(self):
        try:
            os.mkdir(self._path)
        except FileExistsError:
            pass
        self._writeMetaInfo()

    @property
    def path(self):
        return self._path

    def _writeMetaInfo(self):
        data = {
            "creator": "io.github.adrientetar.ufoLib2",
            "formatVersion": 3,
        }
        path = os.path.join(self._path, METAINFO_FILENAME)
        with open(path, "wb") as file:
            plistlib.dump(data, file)

    # layers

    def deleteGlyphSet(self, layerName):
        dirName = self._layerContents[layerName]
        path = os.path.join(self._path, dirName)
        shutil.rmtree(path)
        del self._layerContents[layerName]

    def getGlyphSet(self, layerName, default=False):
        if layerName in self._layerContents:
            dirName = self._layerContents[layerName]
        elif default:
            dirName = DEFAULT_GLYPHS_DIRNAME
        else:
            # TODO: cache this
            existing = set(d.lower() for d in self._layerContents.values())
            dirName = self._layerContents[layerName] = userNameToFileName(
                layerName, existing=existing, prefix="glyphs.")
        path = os.path.join(self._path, dirName)
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        return GlyphSet(path)

    def writeLayerContents(self, layerOrder):
        """
        This must be called after all glyph sets have been written.
        """
        data = []
        for name in layerOrder:
            if data:
                dirName = self._layerContents[name]
            else:
                dirName = DEFAULT_GLYPHS_DIRNAME
            data.append((name, dirName))
        assert data
        path = os.path.join(self._path, LAYERCONTENTS_FILENAME)
        with open(path, "wb") as file:
            plistlib.dump(data, file)

    # bin

    def deleteData(self, fileName):
        path = os.path.join(self._path, DATA_DIRNAME, fileName)
        os.remove(path)

    def deleteImage(self, fileName):
        path = os.path.join(self._path, IMAGES_DIRNAME, fileName)
        os.remove(path)

    def writeData(self, fileName, data):
        path = os.path.join(self._path, DATA_DIRNAME, fileName)
        with open(path, "wb") as file:
            plistlib.dump(data, file)

    def writeImage(self, fileName, data):
        path = os.path.join(self._path, IMAGES_DIRNAME, fileName)
        with open(path, "wb") as file:
            plistlib.dump(data, file)

    # single writes

    def writeFeatures(self, text):
        path = os.path.join(self._path, FEATURES_FILENAME)
        if text:
            with open(path, "w") as file:
                file.write(text)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def writeGroups(self, data):
        path = os.path.join(self._path, GROUPS_FILENAME)
        if data:
            with open(path, "wb") as file:
                plistlib.dump(data, file)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def writeInfo(self, data):
        path = os.path.join(self._path, FONTINFO_FILENAME)
        if data:
            with open(path, "wb") as file:
                plistlib.dump(data, file)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def writeKerning(self, data):
        path = os.path.join(self._path, KERNING_FILENAME)
        if data:
            with open(path, "wb") as file:
                plistlib.dump(data, file)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def writeLib(self, data):
        path = os.path.join(self._path, LIB_FILENAME)
        if data:
            with open(path, "wb") as file:
                plistlib.dump(data, file)
        else:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
