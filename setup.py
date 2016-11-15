#!/usr/bin/env python

from setuptools import setup

setup(name = "DesignSpaceDocument",
      version = "0.1",
      description = "Python object to read, write and edit MutatorMath designspace data.",
      author = "Erik van Blokland",
      author_email = "erik@letterror.com",
      url = "https://github.com/LettError/designSpaceDocument",
      license = "MIT",
      packages = [
              "designSpaceDocument",
      ],
      package_dir = {"":"Lib"},
)
