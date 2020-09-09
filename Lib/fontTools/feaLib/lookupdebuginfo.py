from typing import NamedTuple
class LookupDebugInfo(NamedTuple):
    """Information about where a lookup came from, to be embedded in a font"""

    location: str
    name: str
    feature: list
