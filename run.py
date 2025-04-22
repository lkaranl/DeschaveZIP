#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adiciona o diretório atual no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from deschavezip.dependency_checker import check_dependencies, show_dependency_error
from deschavezip.main import main

if __name__ == "__main__":
    # Verifica dependências antes de iniciar o aplicativo
    if not check_dependencies():
        show_dependency_error()
        sys.exit(1)
    
    sys.exit(main()) 