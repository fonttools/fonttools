from fontTools.misc.py23 import *

__all__ = ['popCount']


def popCount(v):
    """Return number of 1 bits (population count) of an integer.

		Uses the algorithm from `HAKMEM item 169 <https://www.inwap.com/pdp10/hbaker/hakmem/hacks.html#item169>`_.

		Args:
			v (int): Value to count.

		Returns:
			Number of 1 bits in the binary representation of ``v``.
    """

    if v > 0xFFFFFFFF:
        return popCount(v >> 32) + popCount(v & 0xFFFFFFFF)

    # HACKMEM 169
    y = (v >> 1) & 0xDB6DB6DB
    y = v - y - ((y >> 1) & 0xDB6DB6DB)
    return (((y + (y >> 3)) & 0xC71C71C7) % 0x3F)
