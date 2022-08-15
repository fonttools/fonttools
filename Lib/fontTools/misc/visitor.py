"""Generic visitor pattern implementation for Python objects."""

import enum


class Visitor(object):

    defaultStop = False

    @classmethod
    def _register(celf, clazzes_attrs):
        assert celf != Visitor, "Subclass Visitor instead."
        if "_visitors" not in celf.__dict__:
            celf._visitors = {}

        def wrapper(method):
            assert method.__name__ == "visit"
            for clazzes,attrs in clazzes_attrs:
                if type(clazzes) != tuple:
                    clazzes = (clazzes,)
                if type(attrs) == str:
                    attrs = (attrs,)
                for clazz in clazzes:
                    _visitors = celf._visitors.setdefault(clazz, {})
                    for attr in attrs:
                        assert attr not in _visitors, (
                            "Oops, class '%s' has visitor function for '%s' defined already."
                            % (clazz.__name__, attr)
                        )
                        _visitors[attr] = method
            return None

        return wrapper

    @classmethod
    def register(celf, clazzes):
        if type(clazzes) != tuple:
            clazzes = (clazzes,)
        return celf._register([(clazzes, (None,))])

    @classmethod
    def register_attr(celf, clazzes, attrs):
        clazzes_attrs = []
        if type(clazzes) != tuple:
            clazzes = (clazzes,)
        if type(attrs) == str:
            attrs = (attrs,)
        for clazz in clazzes:
            clazzes_attrs.append((clazz, attrs))
        return celf._register(clazzes_attrs)

    @classmethod
    def register_attrs(celf, clazzes_attrs):
        return celf._register(clazzes_attrs)

    @classmethod
    def _visitorsFor(celf, thing, _default={}):
        typ = type(thing)

        for celf in celf.mro():

            _visitors = getattr(celf, "_visitors", None)
            if _visitors is None:
                break

            m = celf._visitors.get(typ, None)
            if m is not None:
                return m

        return _default

    def visitObject(self, obj, *args, **kwargs):
        keys = sorted(vars(obj).keys())
        _visitors = self._visitorsFor(obj)
        defaultVisitor = _visitors.get("*", None)
        for key in keys:
            if key[0] == "_":
                continue
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

    def visitLeaf(self, obj, *args, **kwargs):
        pass

    def visit(self, obj, *args, **kwargs):
        visitorFunc = self._visitorsFor(obj).get(None, None)
        if visitorFunc is not None:
            ret = visitorFunc(self, obj, *args, **kwargs)
            if ret == False or (ret is None and self.defaultStop):
                return
        if hasattr(obj, "__dict__") and not isinstance(obj, enum.Enum):
            self.visitObject(obj, *args, **kwargs)
        elif isinstance(obj, list):
            self.visitList(obj, *args, **kwargs)
        else:
            self.visitLeaf(obj, *args, **kwargs)
