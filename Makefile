all:
	./setup.py build

dist:
	./setup.py sdist bdist_wheel

install:
	pip install --ignore-installed .

install-user:
	pip install --ignore-installed --user .

uninstall:
	pip uninstall --yes fonttools

check: all
	pytest

clean:
	./setup.py clean --all

docs:
	cd Doc && $(MAKE) html

.PHONY: all dist install install-user uninstall check clean docs
