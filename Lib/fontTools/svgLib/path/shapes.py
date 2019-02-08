def _PreferNonZero(*args):
  for arg  in args:
    if arg != 0:
      return arg
  return 0.

def _ntos(n):
  # %f likes to add unnecessary 0's, %g isn't consistent about # decimals
  return ('%.3f' % n).rstrip('0').rstrip('.')

class PathBuilder(object):
  def __init__(self):
    self.pathes = []

  def StartPath(self, initial_path=''):
    self.pathes.append(initial_path)

  def EndPath(self):
    self._Add('z')

  def _Add(self, path_snippet):
    path = self.pathes[-1]
    if path:
      path += ' ' + path_snippet
    else:
      path = path_snippet
    self.pathes[-1] =  path

  def _move(self, c, x, y):
    self._Add('%s%s,%s' % (c, _ntos(x), _ntos(y)))

  def M(self, x, y):
    self._move('M', x, y)

  def m(self, x, y):
    self._move('m', x, y)

  def _arc(self, c, rx, ry, x, y, large_arc):
    self._Add('%s%s,%s 0 %d 1 %s,%s' % (c, _ntos(rx), _ntos(ry), large_arc,
                                        _ntos(x), _ntos(y)))

  def A(self, rx, ry, x, y, large_arc = 0):
    self._arc('A', rx, ry, x, y, large_arc)

  def a(self, rx, ry, x, y, large_arc = 0):
    self._arc('a', rx, ry, x, y, large_arc)

  def _vhline(self, c, x):
    self._Add('%s%s' % (c, _ntos(x)))

  def H(self, x):
    self._vhline('H', x)

  def h(self, x):
    self._vhline('h', x)

  def V(self, y):
    self._vhline('V', y)

  def v(self, x):
    self._vhline('v', y)

  def _ParseRect(self, rect):
    x = float(rect.attrib.get('x', 0))
    y = float(rect.attrib.get('y', 0))
    w = float(rect.attrib.get('width'))
    h = float(rect.attrib.get('height'))
    rx = float(rect.attrib.get('rx', 0))
    ry = float(rect.attrib.get('ry', 0))

    rx = _PreferNonZero(rx, ry)
    ry = _PreferNonZero(ry, rx)
    # TODO there are more rules for adjusting rx, ry

    self.StartPath()
    self.M(x + rx, y)
    self.H(x + w -rx)
    if rx > 0:
      self.A(rx, ry, x + w, y + ry)
    self.V(y + h -ry)
    if rx > 0:
      self.A(rx, ry, x + w - rx, y + h)
    self.H(x + rx)
    if rx > 0:
      self.A(rx, ry, x, y + h - ry)
    self.V(y + ry)
    if rx > 0:
      self.A(rx, ry, x + rx, y)
    self.EndPath()

  def _ParsePath(self, path):
    if 'd' in path.attrib:
      self.StartPath(initial_path=path.attrib['d'])

  def _ParsePolygon(self, poly):
    if 'points' in poly.attrib:
      self.StartPath('M' + poly.attrib['points'])
      self.EndPath()

  def _ParseCircle(self, circle):
    cx = float(circle.attrib.get('cx', 0))
    cy = float(circle.attrib.get('cy', 0))
    r = float(circle.attrib.get('r'))

    # arc doesn't seem to like being a complete shape, draw two halves
    self.StartPath()
    self.M(cx - r, cy)
    self.A(r, r, cx + r, cy, large_arc=1)
    self.A(r, r, cx - r, cy, large_arc=1)

  def AddPathFromElement(self, el):
    tag = el.tag
    if '}' in el.tag:
      tag = el.tag.split('}', 1)[1]  # from https://bugs.python.org/issue18304
    parse_fn = getattr(self, '_Parse%s' % tag.lower().capitalize(), None)
    if not callable(parse_fn):
      return False
    parse_fn(el)
    return True

