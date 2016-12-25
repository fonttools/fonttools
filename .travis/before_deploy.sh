#!/bin/bash

set -e
set -x

if [[ $BUILD_DIST == true ]]; then
	python -m pip install --upgrade wheel
	python setup.py sdist bdist_wheel
fi
