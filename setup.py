#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from glob import glob
from os.path import basename, splitext

############
#  https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/
from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = Path(this_directory / "README.md").read_text()
############

setup(
    packages=find_packages(),
    package_data={"": []},
    include_package_data=True,
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    project_urls={
        "Documentation": "",
        "Changelog": "",
        "Issue Tracker": "",
    },
)
