#!/bin/sh

# exit if any subcommand return non-zero status
set -e

# Choose python version
if test "x$1" = x-3; then
	PYTHON=python3
	shift
elif test "x$1" = x-2; then
	PYTHON=python2
	shift
fi
test "x$PYTHON" = x && PYTHON=python

# Find tests
FILTERS=
for arg in "$@"; do
	test "x$FILTERS" != x && FILTERS="$FILTERS or "
	FILTERS="$FILTERS$arg"
done

# Run tests
if [ -z "$FILTERS" ]; then
	$PYTHON setup.py test
else
	$PYTHON setup.py test --addopts="-k \"$FILTERS\""
fi
