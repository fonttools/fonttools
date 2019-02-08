def _PreferNonZero(*args):
  for arg  in args:
    if arg != 0:
      return arg
  return 0

# TODO float movement
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
    self._Add('%s%d,%d' % (c, x, y))

  def M(self, x, y):
    self._move('M', x, y)

  def m(self, x, y):
    self._move('m', x, y)

  def _arc(self, c, rx, ry, x, y):
    self._Add('%s%d,%d 0 0 1 %d,%d' % (c, rx, ry, x, y))

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

  def _ParseRect(self, rect):
    # TODO what format(s) do these #s come in?
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

  def AddPathFromElement(self, el):
    tag = el.tag
    if '}' in el.tag:
      tag = el.tag.split('}', 1)[1]  # from https://bugs.python.org/issue18304
    parse_fn = getattr(self, '_Parse%s' % tag.lower().capitalize(), None)
    if callable(parse_fn):
      parse_fn(el)
