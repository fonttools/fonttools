import attr
from typing import Optional, Union


@attr.s(slots=True)
class Guideline(object):
    x = attr.ib(type=Union[int, float])
    y = attr.ib(type=Union[int, float])
    angle = attr.ib(type=Union[int, float])
    name = attr.ib(default=None, type=Optional[str])
    color = attr.ib(default=None, type=Optional[str])
    identifier = attr.ib(default=None, type=Optional[str])
