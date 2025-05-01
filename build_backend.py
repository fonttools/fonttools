import os

from setuptools import build_meta as _orig
from setuptools.build_meta import *


def should_build_with_cython(config_settings) -> bool:
    if config_settings:
        value = config_settings.get("FONTTOOLS_WITH_CYTHON", "False")
        return str(value).lower() in {"1", "true", "yes"}
    env = os.environ.get("FONTTOOLS_WITH_CYTHON")
    if str(env).lower() in {"1", "true", "yes"}:
        return True
    return False


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    build_with_cython = should_build_with_cython(config_settings)
    if build_with_cython:
        os.environ["FONTTOOLS_WITH_CYTHON"] = "True"
    return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)


def get_requires_for_build_wheel(config_settings=None):
    requires = _orig.get_requires_for_build_wheel(config_settings)
    if should_build_with_cython(config_settings):
        requires.append("Cython")
    return requires
