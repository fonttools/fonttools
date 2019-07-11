#!/bin/sh

# exit if any subcommand return non-zero status
set -e

# Choose python version
if test "x$1" = x-3; then
	PYTHON=py3
	shift
elif test "x$1" = x-2; then
	PYTHON=py2
	shift
fi
test "x$PYTHON" = x && PYTHON=py

# Find tests
FILTERS=
for arg in "$@"; do
	test "x$FILTERS" != x && FILTERS="$FILTERS or "
	FILTERS="$FILTERS$arg"
done

# Run tests
if [ -z "$FILTERS" ]; then
	tox --develop -e $PYTHON
else
	tox --develop -e $PYTHON -- -k "$FILTERS"
fi
