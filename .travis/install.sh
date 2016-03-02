#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    brew update || brew update
    (brew list | grep -q 'pyenv') || brew install pyenv
    brew outdated pyenv || brew upgrade pyenv

    if which -s pyenv; then
        eval "$(pyenv init -)"
    fi

    case "${TOXENV}" in
        py27)
            curl -O https://bootstrap.pypa.io/get-pip.py
            python get-pip.py --user
            ;;
        py33)
            pyenv install 3.3.6
            pyenv global 3.3.6
            ;;
        py34)
            pyenv install 3.4.3
            pyenv global 3.4.3
            ;;
        py35)
            pyenv install 3.5.0
            pyenv global 3.5.0
            ;;
        pypy)
            pyenv install pypy-4.0.1
            pyenv global pypy-4.0.1
            ;;
    esac
    pyenv rehash
    python -m pip install --user virtualenv
else
    # install pyenv to get latest pypy
    if [[ "${TOXENV}" == "pypy" ]]; then
        git clone https://github.com/yyuu/pyenv.git ~/.pyenv
        PYENV_ROOT="$HOME/.pyenv"
        PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
        pyenv install pypy-4.0.1
        pyenv global pypy-4.0.1
    fi
    pip install virtualenv
fi

python -m virtualenv ~/.venv
source ~/.venv/bin/activate
pip install -r dev-requirements.txt
