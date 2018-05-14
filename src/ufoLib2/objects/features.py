import attr
from typing import Optional


@attr.s(slots=True)
class Features(object):
    text = attr.ib(default="", type=str)
