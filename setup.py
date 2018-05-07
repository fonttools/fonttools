#!/usr/bin/env python
from setuptools import setup, find_packages


with open('README.rst', 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ufoLib2",
    version="0.1.0.dev0",
    description="ufoLib2 is a UFO font library.",
    long_description=long_description,
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="https://github.com/adrientetar/ufoLib2",
    license="Apache 2.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "fonttools>=3.24.0",
        "attrs>=17.3.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: Fonts",
        "License :: OSI Approved :: Apache Software License",
    ],
)
