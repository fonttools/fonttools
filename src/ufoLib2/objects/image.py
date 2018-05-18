import attr
from typing import Optional
from ufoLib2.objects.misc import Transformation


def _to_optional_transformation(v):
    if v is not None and not isinstance(v, Transformation):
        return Transformation(*v)


@attr.s(slots=True)
class Image(object):
    fileName = attr.ib(default=None, type=Optional[str])
    _transformation = attr.ib(
        default=None,
        convert=_to_optional_transformation,
        type=Optional[Transformation],
    )
    color = attr.ib(default=None, type=Optional[str])

    @property
    def transformation(self):
        return self._transformation

    @transformation.setter
    def transformation(self, value):
        self._transformation = _to_optional_transformation(value)

    def clear(self):
        self.fileName = None
        self._transformation = None
        self.color = None
