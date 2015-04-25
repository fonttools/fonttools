#!/bin/sh

# Choose python version
if test "x$1" = x-3; then
	PYTHON=python3
	shift
elif test "x$1" = x-2; then
	PYTHON=python2
	shift
fi
test "x$PYTHON" = x && PYTHON=python

# Setup environment
DIR=`dirname "$0"`
cd "$DIR/Lib"
PYTHONPATH=".:$PYTHONPATH"
export PYTHONPATH

# Find tests
FILTER=
for arg in "$@"; do
	test "x$FILTER" != x && FILTER="$FILTER|"
	FILTER="$FILTER$arg"
done

test "x$FILTER" = "x" && FILTER=.
TESTS=`grep -r --include='*.py' -l -e doctest -e unittest * | grep -E "$FILTER"`

ret=0
FAILS=
for test in $TESTS; do
	echo "Running tests in $test"
	test=`echo "$test" | sed 's@[/\\]@.@g;s@[.]py$@@'`
	if ! $PYTHON -m $test -v; then
		ret=$((ret+1))
		FAILS="$FAILS
$test"
	fi
done
	echo
	echo "SUMMARY:"
if test $ret = 0; then
	echo "All tests passed."
else
	echo "$ret source file(s) had tests failing:$FAILS" >&2
fi
exit $ret
