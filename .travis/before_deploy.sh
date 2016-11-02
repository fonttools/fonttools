#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate

if [[ $BUILD_DIST == true ]]; then
	python setup.py sdist bdist_wheel
fi
