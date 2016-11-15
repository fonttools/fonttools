#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == "Darwin" || "${TOXENV}" == "pypy" || "${TOXENV}" == "jython" ]]; then
    PYENV_ROOT="$HOME/.pyenv"
    PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

if [[ "${TOXENV}" == "jython" ]]; then
    # tox is not working with Jython, so here we simply call py.test ourselves.
    # See: https://bitbucket.org/hpk42/tox/issues/326/oserror-not-a-directory-when-creating-env
    # We also ignore any error for now, until we fix the many test failures...
    pyenv global jython-2.7.1b3
    jython -m pytest || true
else
    source ~/.venv/bin/activate
    tox
fi