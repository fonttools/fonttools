#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    # install pyenv from the git repo (quicker than using brew)
    git clone https://github.com/yyuu/pyenv.git ~/.pyenv
    PYENV_ROOT="$HOME/.pyenv"
    PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"

    case "${TOXENV}" in
        py27)
            # install pip on the system python
            curl -O https://bootstrap.pypa.io/get-pip.py
            python get-pip.py --user
            ;;
        py34)
            pyenv install 3.4.5
            pyenv global 3.4.5
            ;;
        py35)
            pyenv install 3.5.2
            pyenv global 3.5.2
            ;;
        pypy)
            pyenv install pypy-5.3.1
            pyenv global pypy-5.3.1
            ;;
    esac
    pyenv rehash
    python -m pip install --user --upgrade pip virtualenv
else
    # on Linux, we only need pyenv to get the latest pypy and jython
    if [[ "${TOXENV}" == "pypy" || "${TOXENV}" == "jython" ]]; then
        git clone https://github.com/yyuu/pyenv.git ~/.pyenv
        PYENV_ROOT="$HOME/.pyenv"
        PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"

        if [[ "${TOXENV}" == "pypy" ]]; then
            pyenv install pypy-5.3.1
            pyenv global pypy-5.3.1
        else
            pyenv install jython-2.7.1b3
            pyenv global jython-2.7.1b3
        fi
        pyenv rehash
    fi
    if [[ "${TOXENV}" == "jython" ]]; then
        # for jython we just run pytest for now, without virtualenv nor tox.
        # See: https://github.com/behdad/fonttools/issues/575
        jython -m pip install pytest
    else
        pip install --upgrade pip virtualenv
    fi
fi

if [[ "${TOXENV}" != "jython" ]]; then
    # activate virtualenv and install test requirements
    python -m virtualenv ~/.venv
    source ~/.venv/bin/activate
    pip install -r dev-requirements.txt
fi
