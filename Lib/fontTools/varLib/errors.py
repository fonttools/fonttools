from enum import Enum, auto
import textwrap


class VarLibMergeFailure(Enum):
    ShouldBeConstant = "some values were different, but should have been the same"
    MismatchedTypes = "data had inconsistent types"
    LengthsDiffer = "a list of objects had inconsistent lengths"
    KeysDiffer = "a list of objects had different keys"
    InconsistentGlyphOrder = "the glyph order was inconsistent between masters"
    FoundANone = "one of the values in a list was empty when it shouldn't have been"
    NotANone = "one of the values in a list was not empty when it should have been"
    UnsupportedFormat = "an OpenType subtable (%s) had a format I didn't expect"
    InconsistentFormat = (
        "an OpenType subtable (%s) had inconsistent formats between masters"
    )
    InconsistentExtensions = "the masters use extension lookups in inconsistent ways"


class VarLibError(Exception):
    """Base exception for the varLib module."""


class VarLibValidationError(VarLibError):
    """Raised when input data is invalid from varLib's point of view."""


class VarLibMergeError(VarLibError):
    """Raised when input data cannot be merged into a variable font."""

    def __init__(self, merger, args):
        self.merger = merger
        self.args = args

    def _master_name(self, ttf, ix):
        if "name" in ttf:
            return ttf["name"].getDebugName(1) + " " + ttf["name"].getDebugName(2)
        elif hasattr(ttf.reader, "file") and hasattr(ttf.reader.file, "name"):
            return ttf.reader.file.name
        else:
            return "master number %i" % ix

    def __str__(self):
        cause, stack = self.args[0], self.args[1:]
        fontnames = [
            self._master_name(ttf, ix) for ix, ttf in enumerate(self.merger.ttfs)
        ]
        context = "".join(reversed(stack))
        details = ""
        reason = cause["reason"].value
        if reason == VarLibMergeFailure.FoundANone:
            offender = [x is None for x in cause["got"]].index(True)
            details = (
                f"\n\nThe problem is likely to be in {fontnames[offender]}:\n"
                f"{stack[0]}=={cause['got']}\n"
            )
        elif "expected" in cause and "got" in cause:
            offender = [x == cause["expected"] for x in cause["got"]].index(False)
            got = cause["got"][offender]
            details = (
                f"\n\nThe problem is likely to be in {fontnames[offender]}:\n"
                f"Expected to see {stack[0]}=={cause['expected']}, instead saw {got}\n"
            )

        if (
            reason == VarLibMergeFailure.UnsupportedFormat
            or reason == VarLibMergeFailure.InconsistentFormat
        ):
            reason = reason % cause["subtable"]
        basic = textwrap.fill(
            f"Couldn't merge the fonts, because {reason}. "
            f"This happened while performing the following operation: {context}",
            width=78,
        )
        return "\n\n" + basic + details


class VarLibCFFDictMergeError(VarLibMergeError):
    """Raised when a CFF PrivateDict cannot be merged."""

    def __init__(self, key, value, values):
        error_msg = (
            f"For the Private Dict key '{key}', the default font value list:"
            f"\n\t{value}\nhad a different number of values than a region font:"
        )
        for region_value in values:
            error_msg += f"\n\t{region_value}"
        self.args = (error_msg,)


class VarLibCFFPointTypeMergeError(VarLibMergeError):
    """Raised when a CFF glyph cannot be merged because of point type differences."""

    def __init__(self, point_type, pt_index, m_index, default_type, glyph_name):
        error_msg = (
            f"Glyph '{glyph_name}': '{point_type}' at point index {pt_index} in "
            f"master index {m_index} differs from the default font point type "
            f"'{default_type}'"
        )
        self.args = (error_msg,)


class VarLibCFFHintTypeMergeError(VarLibMergeError):
    """Raised when a CFF glyph cannot be merged because of hint type differences."""

    def __init__(self, hint_type, cmd_index, m_index, default_type, glyph_name):
        error_msg = (
            f"Glyph '{glyph_name}': '{hint_type}' at index {cmd_index} in "
            f"master index {m_index} differs from the default font hint type "
            f"'{default_type}'"
        )
        self.args = (error_msg,)


class VariationModelError(VarLibError):
    """Raised when a variation model is faulty."""
