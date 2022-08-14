from fontTools.ttLib import TTFont

class Visitor(object):

	defaultStop = False

	@classmethod
	def register(celf, clazzes, attrs=(None,)):
		assert celf != Visitor, 'Subclass Visitor instead.'
		if '_visitors' not in celf.__dict__:
			celf._visitors = {}
		if type(clazzes) != tuple:
			clazzes = (clazzes,)
		if type(attrs) == str:
			attrs = (attrs,)
		def wrapper(method):
			assert method.__name__ == 'visit'
			done = []
			for clazz in clazzes:
				if clazz in done: continue # Support multiple names of a clazz
				done.append(clazz)
				_visitors = celf._visitors.setdefault(clazz, {})
				for attr in attrs:
					assert attr not in _visitors, \
						"Oops, class '%s' has visitor function for '%s' defined already." % (clazz.__name__, attr)
					_visitors[attr] = method
			return None
		return wrapper

	@classmethod
	def _visitorsFor(celf, thing, _default={}):
		typ = type(thing)

		for celf in celf.mro():

			_visitors = getattr(celf, '_visitors', None)
			if _visitors is None:
				break;

			m = celf._visitors.get(typ, None)
			if m is not None:
				return m

		return _default

	def visitObject(self, obj, *args, **kwargs):
		keys = sorted(vars(obj).keys())
		_visitors = self._visitorsFor(obj)
		defaultVisitor = _visitors.get('*', None)
		for key in keys:
			value = getattr(obj, key)
			visitorFunc = _visitors.get(key, defaultVisitor)
			if visitorFunc is not None:
				ret = visitorFunc(self, obj, key, value, *args, **kwargs)
				if ret == False or (ret is None and self.defaultStop):
				  continue
			self.visitAttr(obj, key, value, *args, **kwargs)

	def visitAttr(self, obj, attr, value, *args, **kwargs):
		self.visit(value, *args, **kwargs)

	def visitList(self, obj, *args, **kwargs):
		for value in obj:
			self.visit(value, *args, **kwargs)

	def visit(self, obj, *args, **kwargs):
		visitorFunc = self._visitorsFor(obj).get(None, None)
		if visitorFunc is not None:
			ret = visitorFunc(self, obj, *args, **kwargs)
			if ret == False or (ret is None and self.defaultStop):
			  return
		if hasattr(obj, '__dict__'):
			self.visitObject(obj, *args, **kwargs)
		elif isinstance(obj, list):
			self.visitList(obj, *args, **kwargs)


class TTVisitor(Visitor):

	def visit(self, obj, *args, **kwargs):
		if hasattr(obj, "ensureDecompiled"):
			obj.ensureDecompiled()
		super().visit(obj, *args, **kwargs)

@TTVisitor.register(TTFont)
def visit(visitor, font):
	if hasattr(font, 'visited'):
		return False
	font.visited = True
	for tag in font.keys():
		visitor.visit(font[tag])
	del font.visited
	return False
