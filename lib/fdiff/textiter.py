#!/usr/bin/env python3

from collections import deque
from itertools import islice


def head(iterable, n):
    """Returns the first n indices of `iterable` as an iterable."""
    return islice(iterable, n)


def tail(iterable, n):
    """Returns the last n indices of `iterable` as an iterable."""
    return iter(deque(iterable, maxlen=n))
