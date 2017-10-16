#!/bin/bash

set -e
set -x

ci_requirements="pip setuptools tox"

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    if [[ ${TOXENV} == *"py27"* ]]; then
        # install pip on the system python
        curl -O https://bootstrap.pypa.io/get-pip.py
        python get-pip.py --user
        # install virtualenv and create virtual environment
        python -m pip install --user virtualenv
        python -m virtualenv .venv/
    elif [[ ${TOXENV} == *"py3"* ]]; then
        # install/upgrade current python3 with homebrew
        if brew list --versions python3 > /dev/null; then
            brew upgrade python3
        else
            brew install python3
        fi
        # create virtual environment
        python3 -m venv .venv/
    else
        echo "unsupported $TOXENV: "${TOXENV}
        exit 1
    fi
    # activate virtual environment
    source .venv/bin/activate
fi

python -m pip install $ci_requirements
