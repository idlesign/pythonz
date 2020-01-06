"""
This packages is to be installed with

    pip install -e .

"""
import io
import os
import re
import sys

from setuptools import setup, find_packages

PATH_BASE = os.path.dirname(__file__)


def read_file(fpath):
    """Reads a file within package directories."""
    with io.open(os.path.join(PATH_BASE, fpath)) as f:
        return f.read()


def get_version():
    """Returns version number, without module import (which can lead to ImportError
    if some dependencies are unavailable before install."""
    contents = read_file(os.path.join('pythonz', '__init__.py'))
    version = re.search('VERSION = \(([^)]+)\)', contents)
    version = version.group(1).replace(', ', '.').strip()
    return version


setup(
    name='pythonz',
    version=get_version(),
    url='https://github.com/idlesign/pythonz',

    description='Source code for pythonz.net',
    long_description=read_file('README.rst'),

    author='Igor `idle sign` Starikov',
    author_email='idlesign@yandex.ru',

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    install_requires=[],
    setup_requires=[] + (['pytest-runner'] if 'test' in sys.argv else []) + [],

    entry_points={
        'console_scripts': ['pythonz = pythonz.manage:main'],
    },

    test_suite='tests',

    tests_require=[
        'pytest',
        'pytest-djangoapp>=0.13.0',
    ],
)
