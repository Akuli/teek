# flake8: noqa

import os

readthedocs = (os.environ.get('READTHEDOCS', None) == 'True')
if not readthedocs:
    # make sure it's installed
    import _tkinter

from setuptools import setup, find_packages


with open('README.md', 'r', encoding='utf-8') as readme:
    markdowns = readme.read()


setup(
    name='tkinder',
    version='0.0.1',
    author='Akuli',
    copyright='Copyright (c) 2018 Akuli',
    description="A pythonic alternative to tkinter",
    long_description=markdowns,
    long_description_content_type='text/markdown',
    keywords='tkinter pythonic',
    url='https://github.com/Akuli/tkinder',
    packages=find_packages(),
)
