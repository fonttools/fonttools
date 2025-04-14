from __future__ import annotations

from fontTools.misc.textTools import byteord, tostr

import re
from bisect import bisect_right
from typing import Literal, TypeVar, overload


try:
    # use unicodedata backport compatible with python2:
    # https://github.com/fonttools/unicodedata2
    from unicodedata2 import *
except ImportError:  # pragma: no cover
    # fall back to built-in unicodedata (possibly outdated)
    from unicodedata import *

from . import Blocks, Scripts, ScriptExtensions, OTTags

__all__ = [
    # names from built-in unicodedata module
    "lookup",
    "name",
    "decimal",
    "digit",
    "numeric",
    "category",
    "bidirectional",
    "combining",
    "east_asian_width",
    "mirrored",
    "decomposition",
    "normalize",
    "unidata_version",
    "ucd_3_2_0",
    # additonal functions
    "block",
    "script",
    "script_extension",
    "script_name",
    "script_code",
    "script_horizontal_direction",
    "ot_tags_from_script",
    "ot_tag_to_script",
]

# Derived from http://www.unicode.org/Public/UNIDATA/BidiMirroring.txt
# cat BidiMirroring.txt | grep "^[0-9A-F]" | sed "s/;//" | awk '{print "    0x"$1": 0x"$2","}'
MIRRORED = {
    0x0028: 0x0029,
    0x0029: 0x0028,
    0x003C: 0x003E,
    0x003E: 0x003C,
    0x005B: 0x005D,
    0x005D: 0x005B,
    0x007B: 0x007D,
    0x007D: 0x007B,
    0x00AB: 0x00BB,
    0x00BB: 0x00AB,
    0x0F3A: 0x0F3B,
    0x0F3B: 0x0F3A,
    0x0F3C: 0x0F3D,
    0x0F3D: 0x0F3C,
    0x169B: 0x169C,
    0x169C: 0x169B,
    0x2039: 0x203A,
    0x203A: 0x2039,
    0x2045: 0x2046,
    0x2046: 0x2045,
    0x207D: 0x207E,
    0x207E: 0x207D,
    0x208D: 0x208E,
    0x208E: 0x208D,
    0x2208: 0x220B,
    0x2209: 0x220C,
    0x220A: 0x220D,
    0x220B: 0x2208,
    0x220C: 0x2209,
    0x220D: 0x220A,
    0x2215: 0x29F5,
    0x221F: 0x2BFE,
    0x2220: 0x29A3,
    0x2221: 0x299B,
    0x2222: 0x29A0,
    0x2224: 0x2AEE,
    0x223C: 0x223D,
    0x223D: 0x223C,
    0x2243: 0x22CD,
    0x2245: 0x224C,
    0x224C: 0x2245,
    0x2252: 0x2253,
    0x2253: 0x2252,
    0x2254: 0x2255,
    0x2255: 0x2254,
    0x2264: 0x2265,
    0x2265: 0x2264,
    0x2266: 0x2267,
    0x2267: 0x2266,
    0x2268: 0x2269,
    0x2269: 0x2268,
    0x226A: 0x226B,
    0x226B: 0x226A,
    0x226E: 0x226F,
    0x226F: 0x226E,
    0x2270: 0x2271,
    0x2271: 0x2270,
    0x2272: 0x2273,
    0x2273: 0x2272,
    0x2274: 0x2275,
    0x2275: 0x2274,
    0x2276: 0x2277,
    0x2277: 0x2276,
    0x2278: 0x2279,
    0x2279: 0x2278,
    0x227A: 0x227B,
    0x227B: 0x227A,
    0x227C: 0x227D,
    0x227D: 0x227C,
    0x227E: 0x227F,
    0x227F: 0x227E,
    0x2280: 0x2281,
    0x2281: 0x2280,
    0x2282: 0x2283,
    0x2283: 0x2282,
    0x2284: 0x2285,
    0x2285: 0x2284,
    0x2286: 0x2287,
    0x2287: 0x2286,
    0x2288: 0x2289,
    0x2289: 0x2288,
    0x228A: 0x228B,
    0x228B: 0x228A,
    0x228F: 0x2290,
    0x2290: 0x228F,
    0x2291: 0x2292,
    0x2292: 0x2291,
    0x2298: 0x29B8,
    0x22A2: 0x22A3,
    0x22A3: 0x22A2,
    0x22A6: 0x2ADE,
    0x22A8: 0x2AE4,
    0x22A9: 0x2AE3,
    0x22AB: 0x2AE5,
    0x22B0: 0x22B1,
    0x22B1: 0x22B0,
    0x22B2: 0x22B3,
    0x22B3: 0x22B2,
    0x22B4: 0x22B5,
    0x22B5: 0x22B4,
    0x22B6: 0x22B7,
    0x22B7: 0x22B6,
    0x22B8: 0x27DC,
    0x22C9: 0x22CA,
    0x22CA: 0x22C9,
    0x22CB: 0x22CC,
    0x22CC: 0x22CB,
    0x22CD: 0x2243,
    0x22D0: 0x22D1,
    0x22D1: 0x22D0,
    0x22D6: 0x22D7,
    0x22D7: 0x22D6,
    0x22D8: 0x22D9,
    0x22D9: 0x22D8,
    0x22DA: 0x22DB,
    0x22DB: 0x22DA,
    0x22DC: 0x22DD,
    0x22DD: 0x22DC,
    0x22DE: 0x22DF,
    0x22DF: 0x22DE,
    0x22E0: 0x22E1,
    0x22E1: 0x22E0,
    0x22E2: 0x22E3,
    0x22E3: 0x22E2,
    0x22E4: 0x22E5,
    0x22E5: 0x22E4,
    0x22E6: 0x22E7,
    0x22E7: 0x22E6,
    0x22E8: 0x22E9,
    0x22E9: 0x22E8,
    0x22EA: 0x22EB,
    0x22EB: 0x22EA,
    0x22EC: 0x22ED,
    0x22ED: 0x22EC,
    0x22F0: 0x22F1,
    0x22F1: 0x22F0,
    0x22F2: 0x22FA,
    0x22F3: 0x22FB,
    0x22F4: 0x22FC,
    0x22F6: 0x22FD,
    0x22F7: 0x22FE,
    0x22FA: 0x22F2,
    0x22FB: 0x22F3,
    0x22FC: 0x22F4,
    0x22FD: 0x22F6,
    0x22FE: 0x22F7,
    0x2308: 0x2309,
    0x2309: 0x2308,
    0x230A: 0x230B,
    0x230B: 0x230A,
    0x2329: 0x232A,
    0x232A: 0x2329,
    0x2768: 0x2769,
    0x2769: 0x2768,
    0x276A: 0x276B,
    0x276B: 0x276A,
    0x276C: 0x276D,
    0x276D: 0x276C,
    0x276E: 0x276F,
    0x276F: 0x276E,
    0x2770: 0x2771,
    0x2771: 0x2770,
    0x2772: 0x2773,
    0x2773: 0x2772,
    0x2774: 0x2775,
    0x2775: 0x2774,
    0x27C3: 0x27C4,
    0x27C4: 0x27C3,
    0x27C5: 0x27C6,
    0x27C6: 0x27C5,
    0x27C8: 0x27C9,
    0x27C9: 0x27C8,
    0x27CB: 0x27CD,
    0x27CD: 0x27CB,
    0x27D5: 0x27D6,
    0x27D6: 0x27D5,
    0x27DC: 0x22B8,
    0x27DD: 0x27DE,
    0x27DE: 0x27DD,
    0x27E2: 0x27E3,
    0x27E3: 0x27E2,
    0x27E4: 0x27E5,
    0x27E5: 0x27E4,
    0x27E6: 0x27E7,
    0x27E7: 0x27E6,
    0x27E8: 0x27E9,
    0x27E9: 0x27E8,
    0x27EA: 0x27EB,
    0x27EB: 0x27EA,
    0x27EC: 0x27ED,
    0x27ED: 0x27EC,
    0x27EE: 0x27EF,
    0x27EF: 0x27EE,
    0x2983: 0x2984,
    0x2984: 0x2983,
    0x2985: 0x2986,
    0x2986: 0x2985,
    0x2987: 0x2988,
    0x2988: 0x2987,
    0x2989: 0x298A,
    0x298A: 0x2989,
    0x298B: 0x298C,
    0x298C: 0x298B,
    0x298D: 0x2990,
    0x298E: 0x298F,
    0x298F: 0x298E,
    0x2990: 0x298D,
    0x2991: 0x2992,
    0x2992: 0x2991,
    0x2993: 0x2994,
    0x2994: 0x2993,
    0x2995: 0x2996,
    0x2996: 0x2995,
    0x2997: 0x2998,
    0x2998: 0x2997,
    0x299B: 0x2221,
    0x29A0: 0x2222,
    0x29A3: 0x2220,
    0x29A4: 0x29A5,
    0x29A5: 0x29A4,
    0x29A8: 0x29A9,
    0x29A9: 0x29A8,
    0x29AA: 0x29AB,
    0x29AB: 0x29AA,
    0x29AC: 0x29AD,
    0x29AD: 0x29AC,
    0x29AE: 0x29AF,
    0x29AF: 0x29AE,
    0x29B8: 0x2298,
    0x29C0: 0x29C1,
    0x29C1: 0x29C0,
    0x29C4: 0x29C5,
    0x29C5: 0x29C4,
    0x29CF: 0x29D0,
    0x29D0: 0x29CF,
    0x29D1: 0x29D2,
    0x29D2: 0x29D1,
    0x29D4: 0x29D5,
    0x29D5: 0x29D4,
    0x29D8: 0x29D9,
    0x29D9: 0x29D8,
    0x29DA: 0x29DB,
    0x29DB: 0x29DA,
    0x29E8: 0x29E9,
    0x29E9: 0x29E8,
    0x29F5: 0x2215,
    0x29F8: 0x29F9,
    0x29F9: 0x29F8,
    0x29FC: 0x29FD,
    0x29FD: 0x29FC,
    0x2A2B: 0x2A2C,
    0x2A2C: 0x2A2B,
    0x2A2D: 0x2A2E,
    0x2A2E: 0x2A2D,
    0x2A34: 0x2A35,
    0x2A35: 0x2A34,
    0x2A3C: 0x2A3D,
    0x2A3D: 0x2A3C,
    0x2A64: 0x2A65,
    0x2A65: 0x2A64,
    0x2A79: 0x2A7A,
    0x2A7A: 0x2A79,
    0x2A7B: 0x2A7C,
    0x2A7C: 0x2A7B,
    0x2A7D: 0x2A7E,
    0x2A7E: 0x2A7D,
    0x2A7F: 0x2A80,
    0x2A80: 0x2A7F,
    0x2A81: 0x2A82,
    0x2A82: 0x2A81,
    0x2A83: 0x2A84,
    0x2A84: 0x2A83,
    0x2A85: 0x2A86,
    0x2A86: 0x2A85,
    0x2A87: 0x2A88,
    0x2A88: 0x2A87,
    0x2A89: 0x2A8A,
    0x2A8A: 0x2A89,
    0x2A8B: 0x2A8C,
    0x2A8C: 0x2A8B,
    0x2A8D: 0x2A8E,
    0x2A8E: 0x2A8D,
    0x2A8F: 0x2A90,
    0x2A90: 0x2A8F,
    0x2A91: 0x2A92,
    0x2A92: 0x2A91,
    0x2A93: 0x2A94,
    0x2A94: 0x2A93,
    0x2A95: 0x2A96,
    0x2A96: 0x2A95,
    0x2A97: 0x2A98,
    0x2A98: 0x2A97,
    0x2A99: 0x2A9A,
    0x2A9A: 0x2A99,
    0x2A9B: 0x2A9C,
    0x2A9C: 0x2A9B,
    0x2A9D: 0x2A9E,
    0x2A9E: 0x2A9D,
    0x2A9F: 0x2AA0,
    0x2AA0: 0x2A9F,
    0x2AA1: 0x2AA2,
    0x2AA2: 0x2AA1,
    0x2AA6: 0x2AA7,
    0x2AA7: 0x2AA6,
    0x2AA8: 0x2AA9,
    0x2AA9: 0x2AA8,
    0x2AAA: 0x2AAB,
    0x2AAB: 0x2AAA,
    0x2AAC: 0x2AAD,
    0x2AAD: 0x2AAC,
    0x2AAF: 0x2AB0,
    0x2AB0: 0x2AAF,
    0x2AB1: 0x2AB2,
    0x2AB2: 0x2AB1,
    0x2AB3: 0x2AB4,
    0x2AB4: 0x2AB3,
    0x2AB5: 0x2AB6,
    0x2AB6: 0x2AB5,
    0x2AB7: 0x2AB8,
    0x2AB8: 0x2AB7,
    0x2AB9: 0x2ABA,
    0x2ABA: 0x2AB9,
    0x2ABB: 0x2ABC,
    0x2ABC: 0x2ABB,
    0x2ABD: 0x2ABE,
    0x2ABE: 0x2ABD,
    0x2ABF: 0x2AC0,
    0x2AC0: 0x2ABF,
    0x2AC1: 0x2AC2,
    0x2AC2: 0x2AC1,
    0x2AC3: 0x2AC4,
    0x2AC4: 0x2AC3,
    0x2AC5: 0x2AC6,
    0x2AC6: 0x2AC5,
    0x2AC7: 0x2AC8,
    0x2AC8: 0x2AC7,
    0x2AC9: 0x2ACA,
    0x2ACA: 0x2AC9,
    0x2ACB: 0x2ACC,
    0x2ACC: 0x2ACB,
    0x2ACD: 0x2ACE,
    0x2ACE: 0x2ACD,
    0x2ACF: 0x2AD0,
    0x2AD0: 0x2ACF,
    0x2AD1: 0x2AD2,
    0x2AD2: 0x2AD1,
    0x2AD3: 0x2AD4,
    0x2AD4: 0x2AD3,
    0x2AD5: 0x2AD6,
    0x2AD6: 0x2AD5,
    0x2ADE: 0x22A6,
    0x2AE3: 0x22A9,
    0x2AE4: 0x22A8,
    0x2AE5: 0x22AB,
    0x2AEC: 0x2AED,
    0x2AED: 0x2AEC,
    0x2AEE: 0x2224,
    0x2AF7: 0x2AF8,
    0x2AF8: 0x2AF7,
    0x2AF9: 0x2AFA,
    0x2AFA: 0x2AF9,
    0x2BFE: 0x221F,
    0x2E02: 0x2E03,
    0x2E03: 0x2E02,
    0x2E04: 0x2E05,
    0x2E05: 0x2E04,
    0x2E09: 0x2E0A,
    0x2E0A: 0x2E09,
    0x2E0C: 0x2E0D,
    0x2E0D: 0x2E0C,
    0x2E1C: 0x2E1D,
    0x2E1D: 0x2E1C,
    0x2E20: 0x2E21,
    0x2E21: 0x2E20,
    0x2E22: 0x2E23,
    0x2E23: 0x2E22,
    0x2E24: 0x2E25,
    0x2E25: 0x2E24,
    0x2E26: 0x2E27,
    0x2E27: 0x2E26,
    0x2E28: 0x2E29,
    0x2E29: 0x2E28,
    0x2E55: 0x2E56,
    0x2E56: 0x2E55,
    0x2E57: 0x2E58,
    0x2E58: 0x2E57,
    0x2E59: 0x2E5A,
    0x2E5A: 0x2E59,
    0x2E5B: 0x2E5C,
    0x2E5C: 0x2E5B,
    0x3008: 0x3009,
    0x3009: 0x3008,
    0x300A: 0x300B,
    0x300B: 0x300A,
    0x300C: 0x300D,
    0x300D: 0x300C,
    0x300E: 0x300F,
    0x300F: 0x300E,
    0x3010: 0x3011,
    0x3011: 0x3010,
    0x3014: 0x3015,
    0x3015: 0x3014,
    0x3016: 0x3017,
    0x3017: 0x3016,
    0x3018: 0x3019,
    0x3019: 0x3018,
    0x301A: 0x301B,
    0x301B: 0x301A,
    0xFE59: 0xFE5A,
    0xFE5A: 0xFE59,
    0xFE5B: 0xFE5C,
    0xFE5C: 0xFE5B,
    0xFE5D: 0xFE5E,
    0xFE5E: 0xFE5D,
    0xFE64: 0xFE65,
    0xFE65: 0xFE64,
    0xFF08: 0xFF09,
    0xFF09: 0xFF08,
    0xFF1C: 0xFF1E,
    0xFF1E: 0xFF1C,
    0xFF3B: 0xFF3D,
    0xFF3D: 0xFF3B,
    0xFF5B: 0xFF5D,
    0xFF5D: 0xFF5B,
    0xFF5F: 0xFF60,
    0xFF60: 0xFF5F,
    0xFF62: 0xFF63,
    0xFF63: 0xFF62,
}


def script(char):
    """Return the four-letter script code assigned to the Unicode character
    'char' as string.

    >>> script("a")
    'Latn'
    >>> script(",")
    'Zyyy'
    >>> script(chr(0x10FFFF))
    'Zzzz'
    """
    code = byteord(char)
    # 'bisect_right(a, x, lo=0, hi=len(a))' returns an insertion point which
    # comes after (to the right of) any existing entries of x in a, and it
    # partitions array a into two halves so that, for the left side
    # all(val <= x for val in a[lo:i]), and for the right side
    # all(val > x for val in a[i:hi]).
    # Our 'SCRIPT_RANGES' is a sorted list of ranges (only their starting
    # breakpoints); we want to use `bisect_right` to look up the range that
    # contains the given codepoint: i.e. whose start is less than or equal
    # to the codepoint. Thus, we subtract -1 from the index returned.
    i = bisect_right(Scripts.RANGES, code)
    return Scripts.VALUES[i - 1]


def script_extension(char):
    """Return the script extension property assigned to the Unicode character
    'char' as a set of string.

    >>> script_extension("a") == {'Latn'}
    True
    >>> script_extension(chr(0x060C)) == {'Nkoo', 'Arab', 'Rohg', 'Thaa', 'Syrc', 'Gara', 'Yezi'}
    True
    >>> script_extension(chr(0x10FFFF)) == {'Zzzz'}
    True
    """
    code = byteord(char)
    i = bisect_right(ScriptExtensions.RANGES, code)
    value = ScriptExtensions.VALUES[i - 1]
    if value is None:
        # code points not explicitly listed for Script Extensions
        # have as their value the corresponding Script property value
        return {script(char)}
    return value


def script_name(code, default=KeyError):
    """Return the long, human-readable script name given a four-letter
    Unicode script code.

    If no matching name is found, a KeyError is raised by default.

    You can use the 'default' argument to return a fallback value (e.g.
    'Unknown' or None) instead of throwing an error.
    """
    try:
        return str(Scripts.NAMES[code].replace("_", " "))
    except KeyError:
        if isinstance(default, type) and issubclass(default, KeyError):
            raise
        return default


_normalize_re = re.compile(r"[-_ ]+")


def _normalize_property_name(string):
    """Remove case, strip space, '-' and '_' for loose matching."""
    return _normalize_re.sub("", string).lower()


_SCRIPT_CODES = {_normalize_property_name(v): k for k, v in Scripts.NAMES.items()}


def script_code(script_name, default=KeyError):
    """Returns the four-letter Unicode script code from its long name

    If no matching script code is found, a KeyError is raised by default.

    You can use the 'default' argument to return a fallback string (e.g.
    'Zzzz' or None) instead of throwing an error.
    """
    normalized_name = _normalize_property_name(script_name)
    try:
        return _SCRIPT_CODES[normalized_name]
    except KeyError:
        if isinstance(default, type) and issubclass(default, KeyError):
            raise
        return default


# The data on script direction is taken from Harfbuzz source code:
# https://github.com/harfbuzz/harfbuzz/blob/3.2.0/src/hb-common.cc#L514-L613
# This in turn references the following "Script_Metadata" document:
# https://docs.google.com/spreadsheets/d/1Y90M0Ie3MUJ6UVCRDOypOtijlMDLNNyyLk36T6iMu0o
RTL_SCRIPTS = {
    # Unicode-1.1 additions
    "Arab",  # Arabic
    "Hebr",  # Hebrew
    # Unicode-3.0 additions
    "Syrc",  # Syriac
    "Thaa",  # Thaana
    # Unicode-4.0 additions
    "Cprt",  # Cypriot
    # Unicode-4.1 additions
    "Khar",  # Kharoshthi
    # Unicode-5.0 additions
    "Phnx",  # Phoenician
    "Nkoo",  # Nko
    # Unicode-5.1 additions
    "Lydi",  # Lydian
    # Unicode-5.2 additions
    "Avst",  # Avestan
    "Armi",  # Imperial Aramaic
    "Phli",  # Inscriptional Pahlavi
    "Prti",  # Inscriptional Parthian
    "Sarb",  # Old South Arabian
    "Orkh",  # Old Turkic
    "Samr",  # Samaritan
    # Unicode-6.0 additions
    "Mand",  # Mandaic
    # Unicode-6.1 additions
    "Merc",  # Meroitic Cursive
    "Mero",  # Meroitic Hieroglyphs
    # Unicode-7.0 additions
    "Mani",  # Manichaean
    "Mend",  # Mende Kikakui
    "Nbat",  # Nabataean
    "Narb",  # Old North Arabian
    "Palm",  # Palmyrene
    "Phlp",  # Psalter Pahlavi
    # Unicode-8.0 additions
    "Hatr",  # Hatran
    "Hung",  # Old Hungarian
    # Unicode-9.0 additions
    "Adlm",  # Adlam
    # Unicode-11.0 additions
    "Rohg",  # Hanifi Rohingya
    "Sogo",  # Old Sogdian
    "Sogd",  # Sogdian
    # Unicode-12.0 additions
    "Elym",  # Elymaic
    # Unicode-13.0 additions
    "Chrs",  # Chorasmian
    "Yezi",  # Yezidi
    # Unicode-14.0 additions
    "Ougr",  # Old Uyghur
}


HorizDirection = Literal["RTL", "LTR"]
T = TypeVar("T")


@overload
def script_horizontal_direction(script_code: str, default: T) -> HorizDirection | T: ...


@overload
def script_horizontal_direction(
    script_code: str, default: type[KeyError] = KeyError
) -> HorizDirection: ...


def script_horizontal_direction(
    script_code: str, default: T | type[KeyError] = KeyError
) -> HorizDirection | T:
    """Return "RTL" for scripts that contain right-to-left characters
    according to the Bidi_Class property. Otherwise return "LTR".
    """
    if script_code not in Scripts.NAMES:
        if isinstance(default, type) and issubclass(default, KeyError):
            raise default(script_code)
        return default
    return "RTL" if script_code in RTL_SCRIPTS else "LTR"


def block(char):
    """Return the block property assigned to the Unicode character 'char'
    as a string.

    >>> block("a")
    'Basic Latin'
    >>> block(chr(0x060C))
    'Arabic'
    >>> block(chr(0xEFFFF))
    'No_Block'
    """
    code = byteord(char)
    i = bisect_right(Blocks.RANGES, code)
    return Blocks.VALUES[i - 1]


def ot_tags_from_script(script_code):
    """Return a list of OpenType script tags associated with a given
    Unicode script code.
    Return ['DFLT'] script tag for invalid/unknown script codes.
    """
    if script_code in OTTags.SCRIPT_EXCEPTIONS:
        return [OTTags.SCRIPT_EXCEPTIONS[script_code]]

    if script_code not in Scripts.NAMES:
        return [OTTags.DEFAULT_SCRIPT]

    script_tags = [script_code[0].lower() + script_code[1:]]
    if script_code in OTTags.NEW_SCRIPT_TAGS:
        script_tags.extend(OTTags.NEW_SCRIPT_TAGS[script_code])
        script_tags.reverse()  # last in, first out

    return script_tags


def ot_tag_to_script(tag):
    """Return the Unicode script code for the given OpenType script tag, or
    None for "DFLT" tag or if there is no Unicode script associated with it.
    Raises ValueError if the tag is invalid.
    """
    tag = tostr(tag).strip()
    if not tag or " " in tag or len(tag) > 4:
        raise ValueError("invalid OpenType tag: %r" % tag)

    if tag in OTTags.SCRIPT_ALIASES:
        tag = OTTags.SCRIPT_ALIASES[tag]

    while len(tag) != 4:
        tag += str(" ")  # pad with spaces

    if tag == OTTags.DEFAULT_SCRIPT:
        # it's unclear which Unicode script the "DFLT" OpenType tag maps to,
        # so here we return None
        return None

    if tag in OTTags.NEW_SCRIPT_TAGS_REVERSED:
        return OTTags.NEW_SCRIPT_TAGS_REVERSED[tag]

    if tag in OTTags.SCRIPT_EXCEPTIONS_REVERSED:
        return OTTags.SCRIPT_EXCEPTIONS_REVERSED[tag]

    # This side of the conversion is fully algorithmic

    # Any spaces at the end of the tag are replaced by repeating the last
    # letter. Eg 'nko ' -> 'Nkoo'.
    # Change first char to uppercase
    script_code = tag[0].upper() + tag[1]
    for i in range(2, 4):
        script_code += script_code[i - 1] if tag[i] == " " else tag[i]

    if script_code not in Scripts.NAMES:
        return None
    return script_code
