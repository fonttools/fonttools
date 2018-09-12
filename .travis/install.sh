#!/bin/bash

set -e
set -x

ci_requirements="pip setuptools tox"

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    if [[ ${TOXENV} == *"py27"* ]]; then
        # install pip on the system python
        curl -O https://bootstrap.pypa.io/get-pip.py
        python get-pip.py --user
        python -m pip install --user virtualenv
        python -m virtualenv .venv/
    elif [[ ${TOXENV} == *"py3"* ]]; then
        # install current python3 with homebrew
        # NOTE: the formula is now named just "python"
        brew install python
        command -v python3
        python3 --version
        python3 -m pip install virtualenv
        python3 -m virtualenv .venv/
    else
        echo "unsupported $TOXENV: "${TOXENV}
        exit 1
    fi
    source .venv/bin/activate
fi

python -m pip install $ci_requirements
