"""Show this help"""
import pkgutil
import sys
from setuptools import find_packages
from pkgutil import iter_modules
import fontTools
import importlib


def describe(pkg):
    try:
        description = __import__(
            "fontTools." + pkg + ".__main__", globals(), locals(), ["__doc__"]
        ).__doc__
        print("fonttools %-10s %s" % (pkg, description), file=sys.stderr)
    except Exception as e:
        return None


def show_help_list():
    path = fontTools.__path__[0]
    for pkg in find_packages(path):
        qualifiedPkg = "fontTools." + pkg
        describe(pkg)
        pkgpath = path + "/" + qualifiedPkg.replace(".", "/")
        for info in iter_modules([pkgpath]):
            describe(pkg + "." + info.name)


if __name__ == "__main__":
    print("fonttools v%s\n" % fontTools.__version__, file=sys.stderr)
    show_help_list()
