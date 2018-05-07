import attr
from collections import OrderedDict
from ufoLib2.objects.layer import Layer


@attr.s(slots=True)
class LayerSet(object):
    _layers = attr.ib(init=False, type=OrderedDict)
    _scheduledForDeletion = attr.ib(default=attr.Factory(set), init=False, repr=False, type=set)

    def __attrs_post_init__(self):
        self._layers = OrderedDict()

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

    @property
    def defaultLayer(self):
        try:
            return next(iter(self))
        except StopIteration:
            pass
        return None

    @defaultLayer.setter
    def defaultLayer(self, layer):
        hasLayer = False
        layers = OrderedDict()
        layers[layer.name] = layer
        for layer_ in self:
            if layer_ == layer:
                hasLayer = True
                continue
            layers[layer_.name] = layer_
        if not hasLayer:
            raise KeyError("layer %r is not in layer set" % layer)
        self._layers = layers

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
