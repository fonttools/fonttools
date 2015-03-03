#!/bin/sh
PYTHONPATH="Lib:$PYTHONPATH"
export PYTHONPATH
TESTS=`git grep -l doctest Lib/`
ret=0
for test in $TESTS; do
	echo "Running tests in $test"
	if ! python -m doctest -v $test; then
		let ret=ret+1
	fi
done
if test $ret != 0; then
	echo "$ret source file(s) had tests failing" >&2
fi
exit $ret
