def _PreferNonZero(*args):
  for arg  in args:
    if arg != 0:
      return arg
  return 0

# TODO float movement
class PathBuilder(object):
  def __init__(self):
    self.pathes = []

  def StartPath(self):
    self.pathes.append('')

  def _Add(self, path_snippet):
    path = self.pathes[-1]
    if path:
      path += ' ' + path_snippet
    else:
      path = path_snippet
    self.pathes[-1] =  path

  def _move(self, c, x, y):
    self._Add('%s%d,%d' % (c, x, y))

  def M(self, x, y):
    self._move('M', x, y)

  def m(self, x, y):
    self._move('m', x, y)

  def _arc(self, c, rx, ry, x, y):
    self._Add('%s%d %d 0 0 1 %d %d' % (c, rx, ry, x, y))

  def A(self, rx, ry, x, y):
    self._arc('A', rx, ry, x, y)

  def a(self, rx, ry, x, y):
    self._arc('a', rx, ry, x, y)

  def _vhline(self, c, x):
    self._Add('%s%d' % (c, x))

  def H(self, x):
    self._vhline('H', x)

  def h(self, x):
    self._vhline('h', x)

  def V(self, y):
    self._vhline('V', y)

  def v(self, x):
    self._vhline('v', y)

  def Rect(self, rect):
    # TODO what format(s) do these #s come in?
    x = float(rect.attrib.get('x', 0))
    y = float(rect.attrib.get('x', 0))
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
    self.V(x + h -ry)
    if rx > 0:
      self.A(rx, ry, x + w, y + ry)
    self.H(x + rx)
    if rx > 0:
      self.A(rx, ry, x, y + h - ry)
    self.V(y + ry)
