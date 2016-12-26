#!/bin/bash

set -e
set -x

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    source .venv/bin/activate
fi

# upload coverage data to Codecov.io
[[ ${TOXENV} == *"-cov"* ]] && tox -e codecov
