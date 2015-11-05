# cu2qu

This library provides functions which take in RoboFab objects (RFonts or their
children) and converts any cubic curves to quadratic. The most useful function
is probably `fonts_to_quadratic`:

```python
from robofab.world import OpenFont
from cu2qu import fonts_to_quadratic
font = OpenFont('MyFont.ufo')
fonts_to_quadratic([font])
```

If interpolation compatibility is a concern, it can be guaranteed during
conversion:

```python
thin_font = OpenFont('MyFont-Thin.ufo')
bold_font = OpenFont('MyFont-Bold.ufo')
fonts_to_quadratic([thin_font, bold_font], compatible=True)
```

Some fonts may need a different error threshold than the default (5 units). This
can also be provided by the caller:

```python
fonts_to_quadratic([font], max_err=2)
fonts_to_quadratic([thin_font, bold_font], compatible=True, max_err=10)
```

`fonts_to_quadratic` returns a string reporting the number of curves of each
length. For example `print fonts_to_quadratic([font])` may print something like:

```
3: 1000
4: 2000
5: 100
```

meaning that the font now contains 1000 curves with three points, 2000 with four
points, and 100 with five. Given multiple fonts, the function will report the
total counts across all fonts.

See the source for functions which operate on glyphs, segments, or just several
points. `FontCollection` classes are also exposed, which allow access into
multiple fonts simultaneously and may be generally useful.
