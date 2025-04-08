#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="deschavezip",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyGObject",
    ],
    package_data={
        "deschavezip.ui": ["*.ui"],
    },
    entry_points={
        "gui_scripts": [
            "deschavezip=deschavezip.main:main",
        ],
    },
    author="Karan Luciano",
    author_email="karanluciano1@gmail.com",
    description="Ferramenta para quebra de senhas de arquivos ZIP com interface GNOME moderna",
    license="MIT",
    keywords="zip, password, cracker, gtk, gnome",
    url="https://github.com/lkaranl/DeschaveZIP",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
) 