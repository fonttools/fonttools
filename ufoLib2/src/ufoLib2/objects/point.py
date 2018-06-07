import attr
from typing import Optional, Union


@attr.s(slots=True)
class Point(object):
    x = attr.ib(type=Union[int, float])
    y = attr.ib(type=Union[int, float])
    type = attr.ib(type=Optional[str])
    smooth = attr.ib(default=False, type=bool)
    name = attr.ib(default=None, type=Optional[str])
    identifier = attr.ib(default=None, type=Optional[str])

    @property
    def segmentType(self):
        # alias for backward compatibility with defcon API
        return self.type
