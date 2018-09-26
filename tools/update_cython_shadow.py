""" Update the embedded Lib/cu2qu/cython.py module with the contents of
the latest cython repository.

Usage:
    $ python tools/update_cython_shadow.py 0.28.5
"""

import requests
import sys


header = b'''\
""" This module is copied verbatim from the "Cython.Shadow" module:
https://github.com/cython/cython/blob/master/Cython/Shadow.py

Cython is licensed under the Apache 2.0 Software License.
"""
'''

try:
    version = sys.argv[1]
except IndexError:
    version = "master"

CYTHON_SHADOW_URL = (
    "https://raw.githubusercontent.com/cython/cython/%s/Cython/Shadow.py"
) % version

r = requests.get(CYTHON_SHADOW_URL, allow_redirects=True)
with open("Lib/cu2qu/cython.py", "wb") as f:
    f.write(header)
    f.write(r.content)
