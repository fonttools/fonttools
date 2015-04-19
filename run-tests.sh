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
cd Lib
PYTHONPATH=".:$PYTHONPATH"
export PYTHONPATH

# Find tests
FILTER=$1
shift
while test "x$#" != x0; do
	FILTER="$FILTER|$1"
	shift
done

test "x$FILTER" = x && FILTER=.
TESTS=`grep -r --include='*.py' -l -e doctest -e unittest * | grep -E "$FILTER"`

ret=0
for test in $TESTS; do
	echo "Running tests in $test"
	test=`echo "$test" | sed 's@[/\\]@.@g;s@[.]py$@@'`
	if ! $PYTHON -m $test -v; then
		ret=$((ret+1))
	fi
done
if test $ret != 0; then
	echo "$ret source file(s) had tests failing" >&2
fi
exit $ret
