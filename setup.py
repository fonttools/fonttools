# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.sdist import sdist as _sdist
import pkg_resources
from distutils import log
import sys
import os
import re
from io import open


needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_wheel = {'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

# Check if minimum required Cython is available.
# For consistency, we require the same as our vendored Cython.Shadow module
cymod = "Lib/cu2qu/cython.py"
cython_version_re = re.compile('__version__ = ["\']([0-9][0-9\w\.]+)["\']')
with open(cymod, "r", encoding="utf-8") as fp:
    for line in fp:
        m = cython_version_re.match(line)
        if m:
            cython_min_version = m.group(1)
            break
    else:
        sys.exit("error: failed to parse cython version in '%s'" % cymod)

required_cython = "cython >= %s" % cython_min_version
try:
    pkg_resources.require(required_cython)
except pkg_resources.ResolutionError:
    has_cython = False
else:
    has_cython = True

# First, check if the CU2QU_WITH_CYTHON environment variable is set.
# Values "1", "true" or "yes" mean that Cython is required and will be used
# to regenerate the *.c sources from which the native extension is built;
# "0", "false" or "no" mean that Cython is not required and no extension
# module will be compiled (i.e. the wheel is pure-python and universal).
# If the variable is not set, then the pre-generated *.c sources that
# are included in the sdist package will be used to try build the extension.
# However, if any error occurs during compilation (e.g. the host
# machine doesn't have the required compiler toolchain installed), the
# installation proceeds without the compiled extensions, but will only have
# the pure-python module.
env_with_cython = os.environ.get("CU2QU_WITH_CYTHON")
with_cython = (
    True if env_with_cython in {"1", "true", "yes"}
    else False if env_with_cython in {"0", "false", "no"}
    else None
)

# command line options --with-cython and --without-cython are also supported.
# They override the environment variable
opt_with_cython = {'--with-cython'}.intersection(sys.argv)
opt_without_cython = {'--without-cython'}.intersection(sys.argv)
if opt_with_cython and opt_without_cython:
    sys.exit(
        "error: the options '--with-cython' and '--without-cython' are "
        "mutually exclusive"
    )
elif opt_with_cython:
    sys.argv.remove("--with-cython")
    with_cython = True
elif opt_without_cython:
    sys.argv.remove("--without-cython")
    with_cython = False


class cython_build_ext(_build_ext):
    """Compile *.pyx source files to *.c using cythonize if Cython is
    installed, else use the pre-generated *.c sources.
    """

    def finalize_options(self):
        if with_cython:
            if not has_cython:
                from distutils.errors import DistutilsSetupError

                raise DistutilsSetupError(
                    "%s is required when using --with-cython" % required_cython
                )

            from Cython.Build import cythonize

            # optionally enable line tracing for test coverage support
            linetrace = os.environ.get("CYTHON_TRACE") == "1"

            self.distribution.ext_modules[:] = cythonize(
                self.distribution.ext_modules,
                force=linetrace or self.force,
                annotate=os.environ.get("CYTHON_ANNOTATE") == "1",
                quiet=not self.verbose,
                compiler_directives={
                    "linetrace": linetrace,
                    "language_level": 3,
                    "embedsignature": True,
                },
            )
        else:
            # replace *.py/.pyx sources with their pre-generated *.c versions
            for ext in self.distribution.ext_modules:
                ext.sources = [re.sub("\.pyx?$", ".c", n) for n in ext.sources]

        _build_ext.finalize_options(self)

    def build_extensions(self):
        if not has_cython:
            log.info(
                "%s is not installed. Pre-generated *.c sources will be "
                "will be used to build the extensions." % required_cython
            )

        try:
            _build_ext.build_extensions(self)
        except Exception as e:
            if with_cython:
                raise
            from distutils.errors import DistutilsModuleError

            # optional compilation failed: we delete 'ext_modules' and make sure
            # the generated wheel is 'pure'
            del self.distribution.ext_modules[:]
            try:
                bdist_wheel = self.get_finalized_command("bdist_wheel")
            except DistutilsModuleError:
                # 'bdist_wheel' command not available as wheel is not installed
                pass
            else:
                bdist_wheel.root_is_pure = True
            log.error('error: building extensions failed: %s' % e)

    def get_source_files(self):
        filenames = _build_ext.get_source_files(self)

        # include pre-generated *.c sources inside sdist, but only if cython is
        # installed (and hence they will be updated upon making the sdist)
        if has_cython:
            for ext in self.extensions:
                filenames.extend(
                    [re.sub("\.pyx?$", ".c", n) for n in ext.sources]
                )
        return filenames


class cython_sdist(_sdist):
    """ Run 'cythonize' on *.pyx sources to ensure the *.c files included
    in the source distribution are up-to-date.
    """

    def run(self):
        if with_cython and not has_cython:
            from distutils.errors import DistutilsSetupError

            raise DistutilsSetupError(
                "%s is required when creating sdist --with-cython"
                % required_cython
            )

        if has_cython:
            from Cython.Build import cythonize

            cythonize(
                self.distribution.ext_modules,
                force=True,  # always regenerate *.c sources
                quiet=not self.verbose,
                compiler_directives={
                    "language_level": 3,
                    "embedsignature": True
                },
            )

        _sdist.run(self)


# don't build extensions if user explicitly requested --without-cython
if with_cython is False:
    extensions = []
else:
    extensions = [
        Extension("cu2qu.cu2qu", ["Lib/cu2qu/cu2qu.py"]),
    ]

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='cu2qu',
    use_scm_version={"write_to": "Lib/cu2qu/_version.py"},
    description='Cubic-to-quadratic bezier curve conversion',
    author="James Godfrey-Kittle, Behdad Esfahbod",
    author_email="jamesgk@google.com",
    url="https://github.com/googlei18n",
    license="Apache License, Version 2.0",
    long_description=long_description,
    packages=find_packages('Lib'),
    package_dir={'': 'Lib'},
    ext_modules=extensions,
    include_package_data=True,
    setup_requires=pytest_runner + wheel + ["setuptools_scm"],
    tests_require=[
        'pytest>=2.8',
    ],
    install_requires=[
        "fonttools>=3.18.0",
        "ufoLib>=2.1.1",
    ],
    extras_require={"cli": ["defcon>=0.4.0"]},
    entry_points={"console_scripts": ["cu2qu = cu2qu.cli:main [cli]"]},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    cmdclass={"build_ext": cython_build_ext, "sdist": cython_sdist},
)
