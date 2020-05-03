"""Show this help"""
import pkgutil
import sys
from setuptools import find_packages
from pkgutil import iter_modules
import fontTools
import importlib


def get_description(pkg):
  try:
    return __import__(pkg+".__main__",globals(),locals(),["__doc__"]).__doc__
  except Exception as e:
    return None

def show_help_list():
  path = fontTools.__path__[0]
  for pkg in find_packages(path):
      qualifiedPkg = "fontTools."+pkg
      description = get_description(qualifiedPkg)
      if description:
        print("fontools %-10s %s" % (pkg, description))
        pkgpath = path + '/' + qualifiedPkg.replace('.', '/')
        if (sys.version_info.major == 3 and sys.version_info.minor < 6):
            for _, name, ispkg in iter_modules([pkgpath]):
                if get_description(pkg+ '.' + name):
                    modules.add(pkg + '.' + name)
        else:
            for info in iter_modules([pkgpath]):
                if get_description(pkg+ '.' + info.name):
                    modules.add(pkg + '.' + info.name)

if __name__ == '__main__':
  print("fonttools v%s\n" % fontTools.__version__)
  show_help_list()
