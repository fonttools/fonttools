from __future__ import absolute_import, unicode_literals
import attr
from fontTools.misc.filenames import userNameToFileName
from fontTools.misc.py23 import open, tounicode
import os
import errno
from ufoLib2 import plistlib
import shutil
from ufoLib2.constants import (
    DATA_DIRNAME,
    DEFAULT_GLYPHS_DIRNAME,
    FEATURES_FILENAME,
    FONTINFO_FILENAME,
    GROUPS_FILENAME,
    KERNING_FILENAME,
    IMAGES_DIRNAME,
    LAYERCONTENTS_FILENAME,
    LIB_FILENAME,
    METAINFO_FILENAME,
)
from ufoLib2.glyphSet import GlyphSet


@attr.s(slots=True)
class UFOWriter(object):
    # TODO: we should probably take path-like objects, for zip etc. support.
    _path = attr.ib(type=str)
    _layerContents = attr.ib(
        default=attr.Factory(dict), init=False, repr=False, type=list
    )

    def __attrs_post_init__(self):
        _ensure_dir(self._path)
        self._writeMetaInfo()

    @property
    def path(self):
        return self._path

    def _writeMetaInfo(self):
        data = {"creator": "io.github.adrientetar.ufoLib2", "formatVersion": 3}
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
            existing = {d.lower() for d in self._layerContents.values()}
            dirName = self._layerContents[layerName] = userNameToFileName(
                tounicode(layerName, "utf-8"),
                existing=existing,
                prefix="glyphs.",
            )
        path = os.path.join(self._path, dirName)
        _ensure_dir(path)
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
        datadir = _ensure_dir(os.path.join(self._path, DATA_DIRNAME))
        path = os.path.join(datadir, fileName)
        with open(path, "wb") as file:
            plistlib.dump(data, file)

    def writeImage(self, fileName, data):
        imagesdir = _ensure_dir(os.path.join(self._path, IMAGES_DIRNAME))
        path = os.path.join(imagesdir, fileName)
        with open(path, "wb") as file:
            plistlib.dump(data, file)

    # single writes

    def writeFeatures(self, text):
        path = os.path.join(self._path, FEATURES_FILENAME)
        if text:
            text = tounicode(text, encoding="utf-8")
            with open(path, "w", encoding="utf-8") as file:
                file.write(text)
        else:
            _ensure_removed(path)

    def writeGroups(self, data):
        path = os.path.join(self._path, GROUPS_FILENAME)
        self._writePlist(path, data)

    def writeInfo(self, data):
        path = os.path.join(self._path, FONTINFO_FILENAME)
        self._writePlist(path, data)

    def writeKerning(self, data):
        # create nested kerning left/right dicts
        kerning = {}
        for (left, right), value in data.items():
            kerning.setdefault(left, {})[right] = value
        path = os.path.join(self._path, KERNING_FILENAME)
        self._writePlist(path, kerning)

    def writeLib(self, data):
        path = os.path.join(self._path, LIB_FILENAME)
        self._writePlist(path, data)

    @staticmethod
    def _writePlist(path, data):
        if data:
            with open(path, "wb") as file:
                plistlib.dump(data, file)
        else:
            _ensure_removed(path)


def _ensure_dir(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return path


def _ensure_removed(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
