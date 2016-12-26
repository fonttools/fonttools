#!/bin/bash

set -e
set -x

# build sdist and wheel distribution packages in ./dist folder.
# Travis runs the `before_deploy` stage before each deployment, but
# we only want to build them once, as we want to use the same
# files for both Github and PyPI
if $(ls ./dist/fonttools*.zip > /dev/null 2>&1) && \
		$(ls ./dist/fonttools*.whl > /dev/null 2>&1); then
	echo "Distribution packages already exists; skipping"
else
	tox -e bdist
fi
