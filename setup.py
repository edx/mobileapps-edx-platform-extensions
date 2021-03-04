#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='mobileapps-edx-platform-extensions',
    version='3.0.0',
    description='Mobile apps management extension for edX platform',
    long_description=open('README.rst').read(),
    author='edX',
    url='https://github.com/edx-solutions/mobileapps-edx-platform-extensions.git',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=2.2,<2.3",
    ],
)
