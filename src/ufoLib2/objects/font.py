import attr
import os
from typing import Optional
from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.objects.dataSet import DataSet
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.imageSet import ImageSet
from ufoLib2.objects.info import Info
from ufoLib2.objects.layerSet import LayerSet
from ufoLib2.reader import UFOReader
from ufoLib2.writer import UFOWriter


@attr.s(slots=True)
class Font(object):
    _path = attr.ib(default=None, type=Optional[str])

    _features = attr.ib(default=None, init=False, repr=False, type=Optional[str])
    _groups = attr.ib(default=None, init=False, repr=False, type=dict)
    _guidelines = attr.ib(default=None, init=False, repr=False, type=list)
    _info = attr.ib(default=None, init=False, repr=False, type=Info)
    _kerning = attr.ib(default=None, init=False, repr=False, type=dict)
    _layers = attr.ib(default=attr.Factory(LayerSet), init=False, repr=False, type=LayerSet)
    _lib = attr.ib(default=None, init=False, repr=False, type=dict)

    _data = attr.ib(init=False, repr=False, type=DataSet)
    _images = attr.ib(init=False, repr=False, type=ImageSet)

    def __attrs_post_init__(self):
        if self._path is not None:
            reader = UFOReader(self._path)
            # load the layers
            for name, dirName in reader.getLayerContents():
                glyphSet = reader.getGlyphSet(dirName)
                self._layers.newLayer(name, glyphSet=glyphSet)
            # load data directory list
            data = reader.getDataDirectoryListing()
            self._data = DataSet(path=self._path, fileNames=data)
            # load images list
            images = reader.getImageDirectoryListing()
            self._images = ImageSet(path=self._path, fileNames=images)
        else:
            self._data = DataSet()
            self._images = ImageSet()

        if not self._layers:
            self._layers.newLayer(DEFAULT_LAYER_NAME)

    def __contains__(self, name):
        return name in self._layers.defaultLayer

    def __delitem__(self, name):
        del self._layers.defaultLayer[name]

    def __getitem__(self, name):
        return self._layers.defaultLayer[name]

    def __iter__(self):
        return iter(self._layers.defaultLayer)

    def __len__(self):
        return len(self._layers.defaultLayer)

    def get(self, name, default=None):
        return self._layers.defaultLayer.get(name, default)

    def keys(self):
        return self._layers.defaultLayer.keys()

    @property
    def features(self):
        if self._features is None:
            if self._path is not None:
                reader = UFOReader(self._path)
                self._features = reader.readFeatures()
            else:
                self._features = ""
        return self._features

    @features.setter
    def features(self, text):
        self._features = text

    @property
    def guidelines(self):
        if self._guidelines is None:
            self.info
        return self._guidelines

    @property
    def groups(self):
        if self._groups is None:
            if self._path is not None:
                reader = UFOReader(self._path)
                self._groups = reader.readGroups()
            else:
                self._groups = {}
        return self._groups

    @property
    def info(self):
        if self._info is None:
            if self._path is not None:
                reader = UFOReader(self._path)
                data = reader.readInfo()
                # split guidelines from the retrieved font info
                guidelines = data.pop("guidelines", [])
                self._info = Info(**data)
                for i in range(len(guidelines)):
                    data = guidelines[i]
                    for key in ("x", "y", "angle"):
                        if key not in data:
                            data[key] = 0
                    guidelines[i] = Guideline(**data)
                self._guidelines = guidelines
            else:
                self._info = Info()
                self._guidelines = []
        return self._info

    @property
    def kerning(self):
        if self._kerning is None:
            if self._path is not None:
                reader = UFOReader(self._path)
                self._kerning = reader.readKerning()
            else:
                self._kerning = {}
        return self._kerning

    @property
    def layers(self):
        return self._layers

    @property
    def lib(self):
        if self._lib is None:
            if self._path is not None:
                reader = UFOReader(self._path)
                self._lib = reader.readLib()
            else:
                self._lib = {}
        return self._lib

    @property
    def data(self):
        return self._data

    @property
    def path(self):
        return self._path

    @property
    def images(self):
        return self._images

    def addGlyph(self, glyph):
        self._layers.defaultLayer.addGlyph(glyph)

    def newGlyph(self, name):
        return self._layers.defaultLayer.newGlyph(name)

    def newLayer(self, name):
        return self._layers.newLayer(name)

    def renameGlyph(self, name, newName, overwrite=False):
        self._layers.defaultLayer.renameGlyph(name, newName, overwrite)

    def renameLayer(self, name, newName, overwrite=False):
        self._layers.renameLayer(name, newName, overwrite)

    def save(self, path=None):
        saveAs = path is not None
        if saveAs:
            if os.path.exists(path):
                raise OSError(errno.EEXIST, "path %r already exists" % path)
        else:
            path = self._path
        if self.layers.defaultLayer.name != DEFAULT_LAYER_NAME:
            assert DEFAULT_LAYER_NAME not in self.layers.layerOrder

        writer = UFOWriter(path)
        # save font attrs
        if self._features is not None or saveAs:
            writer.writeFeatures(self.features)
        if self._groups is not None or saveAs:
            writer.writeGroups(self.groups)
        if self._info is not None or saveAs:
            info = attr.asdict(
                self.info, filter=attr.filters.exclude(type(None)))
            if self.guidelines:
                info["guidelines"] = [
                    attr.asdict(g, filter=attr.filters.exclude(
                        type(None))) for g in self.guidelines]
            writer.writeInfo(info)
        if self._kerning is not None or saveAs:
            writer.writeKerning(self.kerning)
        if self._lib is not None or saveAs:
            writer.writeLib(self.lib)
        # save the layers
        self._layers.save(writer, saveAs=saveAs)
        # save bin parts
        self._data.save(writer, saveAs=saveAs)
        self._images.save(writer, saveAs=saveAs)

        self._path = path
