#!/bin/sh
cd Lib
PYTHONPATH=".:$PYTHONPATH"
export PYTHONPATH
TESTS=`git grep -l doctest`
ret=0
for test in $TESTS; do
	echo "Running tests in $test"
	test=`echo "$test" | sed 's@[/\\]@.@g;s@[.]py$@@'`
	if ! python -m $test -v; then
		ret=$((ret+1))
	fi
done
if test $ret != 0; then
	echo "$ret source file(s) had tests failing" >&2
fi
exit $ret
