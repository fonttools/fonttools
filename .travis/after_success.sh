#!/bin/bash

set -e
set -x

# upload coverage data to Codecov.io
[[ ${TOXENV} == *"-cov"* ]] && python -m tox -e codecov
