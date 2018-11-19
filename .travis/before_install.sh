#!/bin/bash

if [[ -n $PYENV_VERSION ]]; then
    wget https://github.com/praekeltfoundation/travis-pyenv/releases/download/${TRAVIS_PYENV_VERSION}/setup-pyenv.sh
    source setup-pyenv.sh
fi

if [[ $TRAVIS_OS_NAME == windows ]]; then
    choco install python${PYTHON_VERSION:0:1}
    # strip the '.' from major.minor version string, e.g. '2.7' -> '27'
    pyver="${PYTHON_VERSION//\./}"
    export PATH=/c/Python${pyver}/Scripts:/c/Python${pyver}/:$PATH
fi