from typing import TYPE_CHECKING

from fontTools import ttLib

if TYPE_CHECKING:
    from ._h_m_t_x import table__h_m_t_x as superclass
else:
    superclass = ttLib.getTableClass("hmtx")


class table__v_m_t_x(superclass):
    """Vertical Metrics table

    The ``vmtx`` table contains per-glyph metrics for the glyphs in a
    ``glyf``, ``CFF ``, or ``CFF2`` table, as needed for vertical text
    layout.

    See also https://learn.microsoft.com/en-us/typography/opentype/spec/vmtx
    """

    headerTag = "vhea"
    advanceName = "height"
    sideBearingName = "tsb"
    numberOfMetricsName = "numberOfVMetrics"
