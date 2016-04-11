#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == "Darwin" || "${TOXENV}" == "pypy" ]]; then
    PYENV_ROOT="$HOME/.pyenv"
    PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

source ~/.venv/bin/activate
tox
