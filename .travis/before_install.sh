#!/bin/bash

if [[ -n "$PYENV_VERSION" ]]; then
    wget https://github.com/praekeltfoundation/travis-pyenv/releases/download/${TRAVIS_PYENV_VERSION}/setup-pyenv.sh
    source setup-pyenv.sh
fi
