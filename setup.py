#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from io import open


with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ufoLib2",
    use_scm_version={"write_to": "src/ufoLib2/_version.py"},
    description="ufoLib2 is a UFO font library.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="https://github.com/adrientetar/ufoLib2",
    license="Apache 2.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    python_requires=">=2.7",
    install_requires=[
        "fonttools>=3.24.0",
        "attrs>=17.3.0",
        "lxml",
        "typing ; python_version<'3.5'",
        "singledispatch ; python_version<'3.4'",
    ],
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: Fonts",
        "License :: OSI Approved :: Apache Software License",
    ],
)
