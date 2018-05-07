import attr
from typing import Union
from ufoLib2.reader import UFOReader


@attr.s(slots=True)
class DataStore(object):
    readf = None
    writef = None
    deletef = None

    _path = attr.ib(default=None, type=str)
    _fileNames = attr.ib(default=attr.Factory(set), repr=False, type=set)
    _data = attr.ib(default=attr.Factory(dict), init=False, type=dict)
    _scheduledForDeletion = attr.ib(default=attr.Factory(set), init=False, repr=False, type=set)

    def __contains__(self, fileName):
        return fileName in self._fileNames

    def __len__(self):
        return len(self._fileNames)

    def __getitem__(self, fileName):
        if fileName not in self._data:
            if fileName not in self._fileNames:
                raise KeyError("%r is not in data store" % fileName)
            reader = UFOReader(self._path)
            self._data[fileName] = self.readf(reader, fileName)
        return self._data[fileName]

    def __setitem__(self, fileName, data):
        # should we forbid overwrite?
        self._data[fileName] = data
        self._fileNames.add(fileName)
        if fileName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(fileName)

    def __delitem__(self, fileName):
        del self._data[fileName]
        self._fileNames.remove(fileName)
        self._scheduledForDeletion.add(fileName)

    def keys(self):
        return set(self._fileNames)

    def save(self, writer, saveAs=False):
        # if in-place, remove deleted data
        if not saveAs:
            for fileName in self._scheduledForDeletion:
                self.deletef(writer, fileName)
        # write data
        for fileName in self._fileNames:
            data = self[fileName]
            self.writef(writer, fileName, data)
        self._scheduledForDeletion = set()


@attr.s(repr=False, slots=True)
class Transformation(object):
    xScale = attr.ib(default=1, type=Union[int, float])
    xyScale = attr.ib(default=0, type=Union[int, float])
    yxScale = attr.ib(default=0, type=Union[int, float])
    yScale = attr.ib(default=1, type=Union[int, float])
    xOffset = attr.ib(default=0, type=Union[int, float])
    yOffset = attr.ib(default=0, type=Union[int, float])

    def __iter__(self):
        yield self.xScale
        yield self.xyScale
        yield self.yxScale
        yield self.yScale
        yield self.xOffset
        yield self.yOffset

    def __repr__(self):
        return "<%r %r %r %r %r %r>" % tuple(self)
