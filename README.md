# cu2qu

This library provides functions which take in RoboFab objects (RFonts or their
children) and converts any cubic curves to quadratic. The most useful function
is probably `fonts_to_quadratic`:

```python
from robofab.world import OpenFont
from cu2qu.rf import fonts_to_quadratic
thin_font = OpenFont('MyFont-Thin.ufo')
bold_font = OpenFont('MyFont-Bold.ufo')
fonts_to_quadratic(thin_font, bold_font)
```

Interpolation compatibility is guaranteed during conversion. If it's not
needed, converting one font at a time may yield more optimized results:

```python
for font in [thin_font, bold_font]:
    fonts_to_quadratic(font)
```

Some fonts may need a different error threshold than the default (0.0025 em).
This can also be provided by the caller:

```python
fonts_to_quadratic(thin_font, bold_font, max_err_em=0.005)
```

```python
for font in [thin_font, bold_font]:
    fonts_to_quadratic(font, max_err_em=0.001)
```

`fonts_to_quadratic` can print a string reporting the number of curves of each
length. For example `fonts_to_quadratic(font, dump_report=True)` may print
something like:

```
3: 1000
4: 2000
5: 100
```

meaning that the font now contains 1000 curves with three points, 2000 with four
points, and 100 with five. Given multiple fonts, the function will report the
total counts across all fonts. You can also accumulate statistics between calls
by providing your own report dictionary:

```python
stats = {}
for font in [thin_font, bold_font]:
    fonts_to_quadratic(font, report=stats)
# "stats" will report combined statistics for both fonts
```

See the source for functions which operate on glyphs and segments.
