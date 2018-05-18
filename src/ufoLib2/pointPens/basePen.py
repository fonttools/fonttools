class AbstractPointPen(object):
    """
    Baseclass for all PointPens.
    """
    __slots__ = ()

    def beginPath(self, identifier=None, **kwargs):
        """Start a new sub path."""
        raise NotImplementedError

    def endPath(self):
        """End the current sub path."""
        raise NotImplementedError

    def addPoint(
        self,
        pt,
        segmentType=None,
        smooth=False,
        name=None,
        identifier=None,
        **kwargs
    ):
        """Add a point to the current sub path."""
        raise NotImplementedError

    def addComponent(
        self, baseGlyphName, transformation, identifier=None, **kwargs
    ):
        """Add a sub glyph."""
        raise NotImplementedError
