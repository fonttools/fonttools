all:
	./setup.py bdist

dist:
	./setup.py sdist

install:
	./setup.py install

install-user:
	./setup.py install --user

check: all
	./run-tests.sh
