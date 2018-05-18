import attr
from collections import namedtuple
from ufoLib2.reader import UFOReader

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping


@attr.s(slots=True)
class DataStore(object):
    readf = None
    writef = None
    deletef = None

    _path = attr.ib(default=None, type=str)
    _fileNames = attr.ib(default=attr.Factory(set), repr=False, type=set)
    _data = attr.ib(default=attr.Factory(dict), init=False, type=dict)
    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, repr=False, type=set
    )

    def __contains__(self, fileName):
        return fileName in self._fileNames

    def __len__(self):
        return len(self._fileNames)

    def __getitem__(self, fileName):
        if fileName not in self._data:
            if fileName not in self._fileNames:
                raise KeyError("%r is not in data store" % fileName)
            reader = UFOReader(self._path)
            self._data[fileName] = self.__class__.readf(reader, fileName)
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
                self.__class__.deletef(writer, fileName)
        # write data
        for fileName in self._fileNames:
            data = self[fileName]
            self.__class__.writef(writer, fileName, data)
        self._scheduledForDeletion = set()

    @property
    def fileNames(self):
        return self._fileNames


class Transformation(
    namedtuple(
        "Transformation",
        ["xScale", "xyScale", "yxScale", "yScale", "xOffset", "yOffset"],
    )
):

    def __repr__(self):
        return "<%s [%r %r %r %r %r %r]>" % ((self.__class__.__name__,) + self)


Transformation.__new__.__defaults__ = (1, 0, 0, 1, 0, 0)


class AttrDictMixin(Mapping):
    """ Read attribute values using mapping interface. For use with Anchors and
    Guidelines classes, where client code expects them to behave as dict.
    """

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __iter__(self):
        for key in attr.fields_dict(self.__class__):
            if getattr(self, key) is not None:
                yield key

    def __len__(self):
        return sum(1 for _ in self)
