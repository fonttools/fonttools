:orphan:
.. _developerinfo:
.. image:: ../../Icons/FontToolsIconGreenCircle.png
   :width: 200px
   :height: 200px
   :alt: Font Tools
   :align: center


fontTools Developer Information
===============================

If you would like to contribute to the development of fontTools, you can clone the repository from GitHub, install the package in 'editable' mode and modify the source code in place. We recommend creating a virtual environment, using the Python 3 `venv <https://docs.python.org/3/library/venv.html>`_ module::

    # download the source code to 'fonttools' folder
    git clone https://github.com/fonttools/fonttools.git
    cd fonttools

    # create new virtual environment called e.g. 'fonttools-venv', or anything you like
    python -m venv fonttools-venv

    # source the `activate` shell script to enter the environment (Un*x)
    . fonttools-venv/bin/activate

    # to activate the virtual environment in Windows `cmd.exe`, do
    fonttools-venv\Scripts\activate.bat

    # install in 'editable' mode
    pip install -e .


.. note::

    To exit a Python virtual environment, enter the command ``deactivate``.

Testing
-------

To run the test suite, you need to install `pytest <http://docs.pytest.org/en/latest/>`__.
When you run the ``pytest`` command, the tests will run against the
installed fontTools package, or the first one found in the
``PYTHONPATH``.

You can also use `tox <https://tox.readthedocs.io/en/latest/>`__ to
automatically run tests on different Python versions in isolated virtual
environments::

    pip install tox
    tox


.. note::

    When you run ``tox`` without arguments, the tests are executed for all the environments listed in the ``tox.ini`` ``envlist``. The Python versions that are not available on your system ``PATH`` will be skipped.

You can specify a particular testing environment list via the ``-e`` option, or the ``TOXENV`` environment variable::

    tox -e py36
    TOXENV="py36-cov,htmlcov" tox


Development Community
---------------------

fontTools development is ongoing in an active community of developers that includes professional developers employed at major software corporations and type foundries as well as hobbyists.

Feature requests and bug reports are always welcome at https://github.com/fonttools/fonttools/issues/

The best place for end-user and developer discussion about the fontTools project is the `fontTools gitter channel <https://gitter.im/fonttools-dev/Lobby>`_. There is also a development https://groups.google.com/d/forum/fonttools-dev mailing list for continuous integration notifications.


History
-------

The fontTools project was started by Just van Rossum in 1999, and was
maintained as an open source project at
http://sourceforge.net/projects/fonttools/. In 2008, Paul Wise (pabs3)
began helping Just with stability maintenance. In 2013 Behdad Esfahbod
began a friendly fork, thoroughly reviewing the codebase and making
changes at https://github.com/behdad/fonttools to add new features and
support for new font formats.


Acknowledgments
---------------

In alphabetical order:

Olivier Berten, Samyak Bhuta, Erik van Blokland, Petr van Blokland,
Jelle Bosma, Sascha Brawer, Tom Byrer, Frédéric Coiffier, Vincent
Connare, Dave Crossland, Simon Daniels, Peter Dekkers, Behdad Esfahbod,
Behnam Esfahbod, Hannes Famira, Sam Fishman, Matt Fontaine, Yannis
Haralambous, Greg Hitchcock, Jeremie Hornus, Khaled Hosny, John Hudson,
Denis Moyogo Jacquerye, Jack Jansen, Tom Kacvinsky, Jens Kutilek,
Antoine Leca, Werner Lemberg, Tal Leming, Peter Lofting, Cosimo Lupo,
Masaya Nakamura, Dave Opstad, Laurence Penney, Roozbeh Pournader, Garret
Rieger, Read Roberts, Guido van Rossum, Just van Rossum, Andreas Seidel,
Georg Seifert, Chris Simpkins, Miguel Sousa, Adam Twardoch, Adrien Tétar, Vitaly Volkov,
Paul Wise.

License
-------

`MIT license <https://github.com/fonttools/fonttools/blob/main/LICENSE>`_.  See the full text of the license for details.

.. |Travis Build Status| image:: https://travis-ci.org/fonttools/fonttools.svg
   :target: https://travis-ci.org/fonttools/fonttools
.. |Appveyor Build status| image:: https://ci.appveyor.com/api/projects/status/0f7fmee9as744sl7/branch/master?svg=true
   :target: https://ci.appveyor.com/project/fonttools/fonttools/branch/master
.. |Coverage Status| image:: https://codecov.io/gh/fonttools/fonttools/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/fonttools/fonttools
.. |PyPI| image:: https://img.shields.io/pypi/v/fonttools.svg
   :target: https://pypi.org/project/FontTools
.. |Gitter Chat| image:: https://badges.gitter.im/fonttools-dev/Lobby.svg
   :alt: Join the chat at https://gitter.im/fonttools-dev/Lobby
   :target: https://gitter.im/fonttools-dev/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
