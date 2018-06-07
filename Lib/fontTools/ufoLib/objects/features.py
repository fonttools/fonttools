import attr


@attr.s(slots=True)
class Features(object):
    text = attr.ib(default="", type=str)
