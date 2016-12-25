#!/bin/bash

set -e
set -x

pip_options="--upgrade"
ci_requirements="pip setuptools tox"

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
        py35)
            pyenv install 3.5.2
            pyenv global 3.5.2
            ;;
    esac
    pyenv rehash

    # add --user option so we don't require sudo
    pip_options="$pip_options --user"
else
    # on Linux, we're already in a virtualenv; no --user required
    :
fi

python -m pip install $pip_options $ci_requirements
