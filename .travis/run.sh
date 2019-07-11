#!/bin/bash

set -e
set -x

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    source .venv/bin/activate
fi

tox

# re-run all the XML-related tests, this time without lxml but using the
# built-in ElementTree library.
if [ -z "$TOXENV" ]; then
    TOXENV="py-nolxml"
else
    # strip additional tox envs after the comma, add -nolxml factor
    TOXENV="${TOXENV%,*}-nolxml"
fi
tox -e $TOXENV -- Tests/ufoLib Tests/misc/etree_test.py Tests/misc/plistlib_test.py
