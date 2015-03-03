#!/bin/sh
git grep -l doctest Lib/ | PYTHONPATH="Lib:$PYTHONPATH" xargs -n1 python
