# flake8: noqa

# to make sure it's there
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
    install_requires=list(get_requirements()),
    packages=find_packages(),
)
