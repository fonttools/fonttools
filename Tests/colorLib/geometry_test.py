from fontTools.colorLib.geometry import Circle


def test_circle_inside_forwards_tolerance():
    """Circle.inside must honor the supplied relative tolerance (#4317)."""
    inner = Circle((0, 0), 10.0005)
    outer = Circle((0, 0), 10)
    # Default tolerance still treats this near-boundary as inside.
    assert inner.inside(outer) is True
    # Strict tolerance=0 must reject a slightly larger inner circle.
    assert inner.inside(outer, tolerance=0) is False
    # A looser requested tolerance must accept it.
    assert inner.inside(outer, tolerance=0.01) is True
