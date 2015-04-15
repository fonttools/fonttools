#!/bin/sh
cd Lib
PYTHONPATH=".:$PYTHONPATH"
export PYTHONPATH
test "x$PYTHON" = x && PYTHON=python
FILTER=$1
test "x$FILTER" = x && FILTER=.
TESTS=`grep -r --include='*.py' -l -e doctest -e unittest * | grep "$FILTER"`
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
