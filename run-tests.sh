#!/bin/sh
PYTHONPATH="Lib:$PYTHONPATH"
export PYTHONPATH
ret=0
git grep -l doctest Lib/ | while read test; do
	echo "Running tests in $test"
	python $test || let ret=ret+1
done
exit $ret
