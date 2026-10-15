from typing import TYPE_CHECKING

from fontTools import ttLib

if TYPE_CHECKING:
    from ._f_p_g_m import table__f_p_g_m as superclass
else:
    superclass = ttLib.getTableClass("fpgm")


class table__p_r_e_p(superclass):
    """Control Value Program table

    The ``prep`` table contains TrueType instructions that can makee font-wide
    alterations to the Control Value Table. It may potentially be executed
    before any glyph is processed.

    See also https://learn.microsoft.com/en-us/typography/opentype/spec/prep
    """

    pass
