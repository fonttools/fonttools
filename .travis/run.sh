#!/bin/bash

set -e
set -x

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    source .venv/bin/activate
fi

tox

# re-run all the XML-related tests, this time without lxml but using the
# built-in ElementTree library.
tox -e ${TOXENV:-py}-nolxml -- Tests/ufoLib Tests/misc/etree_test.py Tests/misc/plistlib_test.py
