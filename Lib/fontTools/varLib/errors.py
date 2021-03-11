class VarLibError(Exception):
    """Base exception for the varLib module."""


class VarLibValidationError(VarLibError):
    """Raised when input data is invalid from varLib's point of view."""


class VarLibMergeError(VarLibError):
    """Raised when input data cannot be merged into a variable font."""


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
