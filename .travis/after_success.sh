#!/bin/bash

set -e
set -x

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    source .venv/bin/activate
fi

# upload coverage data to Codecov.io
[[ ${TOXENV} == *"-cov"* ]] && tox -e codecov

# if tagged commit, create distribution packages and deploy to PyPI
if [ -n "$TRAVIS_TAG" ] && [ "$TRAVIS_REPO_SLUG" == "fonttools/fonttools" ] && [ "$BUILD_DIST" == true ]; then
    tox -e pypi
fi
