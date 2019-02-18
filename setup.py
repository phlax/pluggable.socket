#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python pluggable.socket
"""

import os

from setuptools import setup, find_namespace_packages

from Cython.Build import cythonize


if 'SETUPPY_CFLAGS' in os.environ:
    os.environ['CFLAGS'] = os.environ['SETUPPY_CFLAGS']


install_requires = [
    'aioredis',
    'pluggable.core',
    'python-rapidjson',
    'umsgpack',
    'websockets',
    'uvloop']
extras_require = {}
extras_require['test'] = [
    "coverage",
    "pytest",
    "pytest-asyncio",
    "pytest-mock",
    "pytest-coverage",
    "codecov",
    "cython",
    "flake8"],

setup(
    name='pluggable.socket',
    version='0.1.0',
    description='pluggable.socket',
    long_description="pluggable.socket",
    url='https://github.com/phlax/pluggable.socket',
    author='Ryan Northey',
    author_email='ryan@synca.io',
    license='GPL3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        ('License :: OSI Approved :: '
         'GNU General Public License v3 or later (GPLv3+)'),
        'Programming Language :: Python :: 3.5',
    ],
    keywords='python pluggable',
    install_requires=install_requires,
    extras_require=extras_require,
    packages=find_namespace_packages(),
    namespace_packages=["pluggable"],
    ext_modules=cythonize("pluggable/socket/*.pyx", annotate=True),
    include_package_data=True)
