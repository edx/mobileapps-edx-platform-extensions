#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='mobileapps-edx-platform-extensions',
    version='1.0.5',
    description='Mobile apps management extension for edX platform',
    long_description=open('README.md').read(),
    author='edX',
    url='https://github.com/edx-solutions/mobileapps-edx-platform-extensions.git',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=1.8",
        'djangorestframework>=3.2.0',
    ],
)
