#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adiciona o diretório atual no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from deschavezip.main import main

if __name__ == "__main__":
    sys.exit(main()) 