from typing import NamedTuple

LOOKUP_DEBUG_INFO_KEY = "com.github.fonttools.feaLib"

class LookupDebugInfo(NamedTuple):
    """Information about where a lookup came from, to be embedded in a font"""

    location: str
    name: str
    feature: list
