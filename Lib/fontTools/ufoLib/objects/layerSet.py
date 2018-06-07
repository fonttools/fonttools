import attr
from collections import OrderedDict
from ufoLib2.objects.layer import Layer
from ufoLib2.constants import DEFAULT_LAYER_NAME
from fontTools.misc.py23 import basestring


def _layersConverter(value):
    # takes an iterable of Layer objects and returns an OrderedDict keyed
    # by layer name
    layers = OrderedDict()
    for layer in value:
        if not isinstance(layer, Layer):
            raise TypeError(
                "expected 'Layer', found '%s'" % type(layer).__name__
            )
        if layer.name in layers:
            raise KeyError("duplicate layer name: '%s'" % layer.name)
        layers[layer.name] = layer
    return layers


@attr.s(slots=True, repr=False)
class LayerSet(object):
    _layers = attr.ib(default=(), converter=_layersConverter, type=OrderedDict)
    _defaultLayer = attr.ib(default=None, type=Layer)
    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, type=set
    )

    def __attrs_post_init__(self):
        if not self._layers:
            # LayerSet is never empty; always contains at least the default
            if self._defaultLayer is not None:
                raise TypeError(
                    "'defaultLayer' argument is invalid with empty LayerSet"
                )
            self._defaultLayer = self.newLayer(DEFAULT_LAYER_NAME)
        elif self._defaultLayer is not None:
            # check that the specified default layer is in the layer set;
            # 'defaultLayer' constructor argument is a string (the name),
            # whereas the 'defaultLayer' property is a Layer object
            default = self._defaultLayer
            if isinstance(default, basestring):
                if default not in self._layers:
                    raise KeyError(default)
                self._defaultLayer = self._layers[default]
            else:
                raise TypeError(
                    "'defaultLayer': expected string, found '%s'"
                    % type(default).__name__
                )
        else:
            if DEFAULT_LAYER_NAME not in self._layers:
                raise ValueError("default layer not specified")
            self._defaultLayer = self._layers[DEFAULT_LAYER_NAME]

    @classmethod
    def load(cls, reader):
        return cls(
            (
                Layer(name=name, glyphSet=glyphSet)
                for name, glyphSet in reader.iterGlyphSets()
            ),
            defaultLayer=reader.getDefaultLayerName(),
        )

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
        return "%s(%s)" % (
            self.__class__.__name__,
            repr(list(self)) if self._layers else "",
        )

    @property
    def defaultLayer(self):
        return self._defaultLayer

    @defaultLayer.setter
    def defaultLayer(self, layer):
        if not isinstance(layer, Layer):
            raise TypeError(
                "expected 'Layer', found '%s'" % type(layer).__name__
            )
        for this in self._layers.values():
            if this is layer:
                break
        else:
            raise KeyError("layer %r is not in layer set" % layer)
        self._defaultLayer = layer

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
                    raise KeyError("target name %r already exists" % newName)
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
            default = layer is defaultLayer
            glyphSet = writer.getGlyphSet(layer.name, default=default)
            layer.save(glyphSet, saveAs=saveAs)
            # do this need a separate call?
            glyphSet.writeLayerInfo(layer)
        writer.writeLayerContents(self.layerOrder)
        self._scheduledForDeletion = set()
