import attr
from collections import OrderedDict
from ufoLib2.objects.layer import Layer
from ufoLib2.constants import DEFAULT_GLYPHS_DIRNAME


@attr.s(slots=True, repr=False)
class LayerSet(object):
    _layers = attr.ib(
        default=attr.Factory(OrderedDict),
        init=False,
        type=OrderedDict)
    _defaultLayerName = attr.ib(default=None, init=False, type=str)
    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, type=set)

    def __contains__(self, name):
        return name in self._layers

    def __delitem__(self, name):
        if name == self.defaultLayer.name:
            raise KeyError("cannot delete default layer %r" % name)
        del self._layers[name]
        self._scheduledForDeletion.add(name)

    def __getitem__(self, name):
        return self._layers[name]

    def __iter__(self):
        return iter(self._layers.values())

    def __len__(self):
        return len(self._layers)

    def get(self, name, default=None):
        return self._layers.get(name, default)

    def keys(self):
        return self._layers.keys()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           repr(list(self)) if self._layers else "")

    @property
    def defaultLayerName(self):
        return self._defaultLayerName  # XXX can be None!

    @defaultLayerName.setter
    def defaultLayerName(self, name):
        if name not in self._layers:
            raise KeyError('layer name "%s" not in layer set' % name)
        self._defaultLayerName = name

    @property
    def defaultLayer(self):
        if self.defaultLayerName is None:
            return
        return self._layers[self.defaultLayerName]

    @defaultLayer.setter
    def defaultLayer(self, layer):
        for this in self:
            if this is layer:
                break
        else:
            raise KeyError("layer %r is not in layer set" % layer)
        self._defaultLayerName = layer.name

    @property
    def layerOrder(self):
        return list(self._layers)

    @layerOrder.setter
    def layerOrder(self, order):
        assert set(order) == set(self._layers)
        layers = OrderedDict()
        for name in order:
            layers[name] = self._layers[name]
        self._layers = layers

    def newLayer(self, name, glyphSet=None):
        if name in self._layers:
            raise KeyError("layer %r already exists" % name)
        self._layers[name] = layer = Layer(name, glyphSet)
        # TODO: should this be done in Layer ctor?
        if glyphSet is not None:
            glyphSet.readLayerInfo(layer)
        if name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(name)
        return layer

    def renameGlyph(self, name, newName, overwrite=False):
        # Note: this would be easier if the glyph contained the layers!
        if name == newName:
            return
        # make sure we're copying something
        if not any(name in layer for layer in self):
            raise KeyError("name %r is not in layer set" % name)
        # prepare destination, delete if overwrite=True or error
        for layer in self:
            if newName in self._layers:
                if overwrite:
                    del layer[newName]
                else:
                    raise KeyError(
                        "target name %r already exists" % newName)
        # now do the move
        for layer in self:
            if name in layer:
                layer[newName] = glyph = layer.pop(name)
                glyph._name = newName

    def renameLayer(self, name, newName, overwrite=False):
        if name == newName:
            return
        if not overwrite and newName in self._layers:
            raise KeyError("target name %r already exists" % newName)
        self._layers[newName] = layer = self._layers.pop(name)
        self._scheduledForDeletion.add(name)
        if newName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(newName)
        layer._name = newName
        if name == self._defaultLayerName:
            self._defaultLayerName = newName

    def save(self, writer, saveAs=False):
        # if in-place, remove deleted layers
        if not saveAs:
            for layerName in self._scheduledForDeletion:
                writer.deleteGlyphSet(layerName)
        # write layers
        defaultLayer = self.defaultLayer
        for layer in self:
            default = layer == defaultLayer
            glyphSet = writer.getGlyphSet(layer.name, default=default)
            layer.save(glyphSet, saveAs=saveAs)
            # do this need a separate call?
            glyphSet.writeLayerInfo(layer)
        writer.writeLayerContents(self.layerOrder)
        self._scheduledForDeletion = set()
