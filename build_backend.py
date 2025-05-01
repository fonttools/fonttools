import os

from setuptools import build_meta as _orig
from setuptools.build_meta import *

USE_CYTHON_ENV_VAR = "FONTTOOLS_WITH_CYTHON"
VAR_TRUTHY_VALUES = {"1", "true", "yes"}


def should_build_with_cython(config_settings) -> bool:
    if config_settings:
        value = config_settings.get(USE_CYTHON_ENV_VAR)
        return str(value).lower() in VAR_TRUTHY_VALUES
    env = os.environ.get(USE_CYTHON_ENV_VAR)
    if str(env).lower() in VAR_TRUTHY_VALUES:
        return True
    return False


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    build_with_cython = should_build_with_cython(config_settings)
    if build_with_cython:
        os.environ[USE_CYTHON_ENV_VAR] = "True"
    return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)


def get_requires_for_build_wheel(config_settings=None):
    requires = _orig.get_requires_for_build_wheel(config_settings)
    if should_build_with_cython(config_settings):
        requires.append("Cython")
    return requires
