import attr
from typing import Optional
from ufoLib2.objects.misc import Transformation


def _to_transformation(v):
    if not isinstance(v, Transformation):
        return Transformation(*v)
    return v


@attr.s(slots=True)
class Image(object):
    fileName = attr.ib(default=None, type=Optional[str])
    _transformation = attr.ib(
        default=Transformation(),
        convert=_to_transformation,
        type=Transformation,
    )
    color = attr.ib(default=None, type=Optional[str])

    @property
    def transformation(self):
        return self._transformation

    @transformation.setter
    def transformation(self, value):
        self._transformation = _to_transformation(value)

    def clear(self):
        self.fileName = None
        self._transformation = None
        self.color = None
