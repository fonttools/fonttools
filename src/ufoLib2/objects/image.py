import attr
from typing import Optional
from ufoLib2.objects.misc import Transformation


@attr.s(slots=True)
class Image(object):
    fileName = attr.ib(type=Optional[str])
    transformation = attr.ib(type=Transformation)
    color = attr.ib(default=None, type=Optional[str])
