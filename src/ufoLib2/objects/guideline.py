import attr
from typing import Optional, Union
from ufoLib2.objects.misc import AttrDictMixin


@attr.s(slots=True)
class Guideline(AttrDictMixin):
    x = attr.ib(default=None, type=Optional[Union[int, float]])
    y = attr.ib(default=None, type=Optional[Union[int, float]])
    angle = attr.ib(default=None, type=Optional[Union[int, float]])
    name = attr.ib(default=None, type=Optional[str])
    color = attr.ib(default=None, type=Optional[str])
    identifier = attr.ib(default=None, type=Optional[str])

    def __attrs_post_init__(self):
        x, y, angle = self.x, self.y, self.angle
        if x is None and y is None:
            raise ValueError("x or y must be present")
        if x is None or y is None:
            if angle is not None:
                raise ValueError(
                    "if 'x' or 'y' are None, 'angle' must not be present"
                )
        if x is not None and y is not None and angle is None:
            raise ValueError(
                "if 'x' and 'y' are defined, 'angle' must be defined"
            )
        if angle is not None and not (0 <= angle <= 360):
            raise ValueError("angle must be between 0 and 360")
