"""
This packages is to be installed with

    pip install -e .

"""
import sys

from setuptools import setup

PYTEST_RUNNER = ['pytest-runner'] if 'test' in sys.argv else []

setup(
    name='pythonz',

    url='https://github.com/idlesign/pythonz',

    author='Igor `idle sign` Starikov',
    author_email='idlesign@yandex.ru',

    tests_require=[
        'pytest',
        'pytest-djangoapp>=0.13.0'
    ],
    test_suite='tests',
    setup_requires=[] + PYTEST_RUNNER,

    entry_points={
        'console_scripts': ['pythonz = manage:manage'],
    },

)
