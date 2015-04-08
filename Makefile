PREFIX=/usr/local

all:
	./setup.py bdist

dist:
	./setup.py sdist

install:
	./setup.py install --prefix=$(PREFIX)

check:
	./run-tests.sh
