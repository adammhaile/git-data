#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('./requirements.txt') as f:
    INSTALL_REQUIRES = f.read().splitlines()

setup(
    name="pygitdata",
    version="0.1.0",
    description="Simple module to pull structured data from git",
    long_description=open('README.md').read(),
    url="https://github.com/adammhaile/gitdata",
    license="LGPL v3.0",
    packages=['gitdata'],
    include_package_data=True,

    install_requires=INSTALL_REQUIRES,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 2.7',
    ],
    dependency_links=[]
)