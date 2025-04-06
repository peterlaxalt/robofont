import weakref


class ImplementationError(Exception):
    pass


def _implementation_get(cls):
    def wrapped(superObject):
        attr = "__implementationObject_%s" % cls.owner
        if not hasattr(superObject, attr):
            setattr(superObject, attr, cls(superObject))
        return getattr(superObject, attr)
    return wrapped


def _implementation_del(cls):
    def wrapped(superObject):
        attr = "__implementationObject_%s" % cls.owner
        if hasattr(superObject, attr):
            delattr(superObject, attr)
    return wrapped


def registerImplementation(cls, superClass, allowsOverwrite=False):
    if cls.owner is None:
        raise ImplementationError("Define an implementation owner")
    if not allowsOverwrite and hasattr(superClass, cls.owner):
        raise ImplementationError("Implementation already exists")
    func = property(fget=_implementation_get(cls), fdel=_implementation_del(cls))
    setattr(superClass, cls.owner, func)


class Implementation(object):

    owner = None

    def __init__(self, superObject, *args, **kwargs):
        self._superObject = weakref.ref(superObject)
        self.init(*args, **kwargs)

    def init(self, *args, **kwargs):
        pass

    def __del__(self):
        self._superObject = None

    def super(self):
        return self._superObject()

    def _get_font(self):
        return self.super().font

    font = property(_get_font)
